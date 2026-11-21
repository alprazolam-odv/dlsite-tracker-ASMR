import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from dlsite_tracker.followed_voices import CatalogState, FollowedVoiceSync, Voice
from dlsite_tracker.http import HttpError
from dlsite_tracker.store import Store


class FollowedVoicesTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.follows_file = root / "follows.json"
        self.cfg = SimpleNamespace(sites=["maniax"], default_work_types=["SOU"], locale="ja_JP",
                                   out_dir=root / "out", images_enabled=False)
        self.store = Store(root / "data.sqlite")
        self.addCleanup(self.store.close)
        self.store.migrate()
        self.alice = Voice("1", "Alice")
        self.bob = Voice("2", "Bob")
        self.pages = {}
        self.rows = {}
        self.page_requests = []
        self.product_requests = []
        self.robots_requests = 0

    def follow(self, *voices):
        self.follows_file.write_text(json.dumps([vars(voice) for voice in voices]), encoding="utf-8")

    def verify_robots(self):
        self.robots_requests += 1

    def get_json(self, url):
        ident = parse_qs(urlsplit(url).query)["workno"][0]
        self.product_requests.append(ident)
        value = self.rows[ident]
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value()
        return [value]

    def catalog(self, _fetcher, site, kind, name, _ident, page):
        self.assertEqual((site, kind), ("maniax", "voice"))
        self.page_requests.append((name, page))
        ids, more = self.pages[(name, page)]
        return {"works": [{"id": ident} for ident in ids], "has_more": more}

    def work(self, ident, *voices):
        return {"workno": ident, "site_id": "maniax", "age_category": 3, "work_type": "SOU",
                "work_name": ident, "creaters": {"voice_by": [vars(voice) for voice in voices]}}

    def run_sync(self, check=False):
        with patch("dlsite_tracker.followed_voices.fetch_creator_page", self.catalog), \
                patch("dlsite_tracker.followed_voices.sync_sales"):
            return FollowedVoiceSync(self.cfg, self.store, self, self.follows_file, lambda _: None).run(check)

    def ids_in_library(self):
        return {row[0] for row in self.store.conn.execute("SELECT workno FROM works")}

    def test_initial_scan_imports_credited_works_and_skips_duplicate_requests(self):
        self.follow(self.alice, self.bob)
        self.pages = {("Alice", 1): (["RJ000001", "RJ000002"], True),
                      ("Alice", 2): (["RJ000003"], False), ("Bob", 1): (["RJ000001", "RJ000004"], False)}
        self.rows = {"RJ000001": self.work("RJ000001", self.alice, self.bob),
                     "RJ000002": self.work("RJ000002", Voice("9", "Alice")),
                     "RJ000003": self.work("RJ000003", Voice("", "Alice")),
                     "RJ000004": self.work("RJ000004", self.bob)}
        self.assertEqual(self.run_sync()["added"], 3)
        self.assertEqual(self.product_requests, list(self.rows))
        self.assertEqual(self.ids_in_library(), {"RJ000001", "RJ000003", "RJ000004"})

        self.page_requests.clear()
        self.product_requests.clear()
        self.assertEqual(self.run_sync()["checked"], 0)
        self.assertEqual(self.robots_requests, 1)
        self.assertEqual(self.page_requests, [])
        self.assertEqual(self.product_requests, [])

    def test_incremental_uses_own_catalog_boundary_and_only_loads_new_metadata(self):
        self.follow(self.alice)
        self.pages = {("Alice", 1): (["RJ000001", "RJ000002"], False)}
        self.rows = {ident: self.work(ident, self.alice) for ident in ("RJ000001", "RJ000002", "RJ000003")}
        self.run_sync()
        self.page_requests.clear()
        self.product_requests.clear()
        self.pages = {("Alice", 1): (["RJ000003", "RJ000001"], True),
                      ("Alice", 2): (["RJ000002"], True)}
        self.assertEqual(self.run_sync(check=True)["added"], 1)
        self.assertEqual(self.page_requests, [("Alice", 1), ("Alice", 2)])
        self.assertEqual(self.product_requests, ["RJ000003"])

    def test_retries_failed_old_product_without_rescanning_history(self):
        self.follow(self.alice)
        self.pages = {("Alice", 1): (["RJ000001"], True), ("Alice", 2): (["RJ000002"], False)}
        self.rows = {"RJ000001": self.work("RJ000001", self.alice), "RJ000002": HttpError("offline")}
        self.assertEqual(self.run_sync()["pending"], 1)
        self.rows["RJ000002"] = self.work("RJ000002", self.alice)
        self.page_requests.clear()
        self.product_requests.clear()
        result = self.run_sync()
        self.assertEqual((result["pending"], result["added"]), (0, 1))
        self.assertEqual(self.page_requests, [])
        self.assertEqual(self.product_requests, ["RJ000002"])

    def test_unfollow_during_fetch_stops_before_saving_result(self):
        self.follow(self.alice)
        self.pages = {("Alice", 1): (["RJ000001", "RJ000002"], True)}

        def unfollow():
            self.follow()
            return self.work("RJ000001", self.alice)

        self.rows["RJ000001"] = unfollow
        self.assertEqual(self.run_sync()["added"], 0)
        self.assertEqual(self.product_requests, ["RJ000001"])
        self.assertEqual(self.ids_in_library(), set())
        self.assertFalse(CatalogState.load(self.store, self.alice.state_key("maniax")).complete)
