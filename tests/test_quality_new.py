import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock

from dlsite_tracker.config import Config
from dlsite_tracker.enrich import scope_allows
from dlsite_tracker.export import export_current
from dlsite_tracker.quality_new import QualitySpec, select_candidates, collect_catalog, run_quality_new
from dlsite_tracker.store import Store


TODAY = date(2026, 11, 21)


def info(released, sales, kind="SOU"):
    return {
        "regist_date": released, "dl_count": sales, "work_type": kind,
        "wishlist_count": 0, "options": "", "rating_precise": None, "rating_count": None,
    }


class QualityNewTest(unittest.TestCase):
    def test_date_scope_and_grace(self):
        spec = QualitySpec.create(30, min_sales=100, protect_days=3, today=TODAY)
        self.assertEqual(spec.start, date(2026, 10, 23))
        entries = {
            "high": info("2026-10-23", 300),
            "boundary": info("2026-11-19", 1),
            "low": info("2026-11-18", 99),
            "unknown_new": info("2026-11-21", None),
            "unknown_old": info("2026-11-18", None),
            "old": info("2026-10-22", 10000),
            "game": info("2026-11-20", 300, "RPG"),
            "future": info("2026-11-22", 600),
        }
        selected, stats = select_candidates(entries, spec)
        self.assertEqual([x[0] for x in selected], ["high", "boundary", "unknown_new"])
        self.assertEqual(stats, {"in_range": 5, "low_sales": 1, "unknown": 1, "protected": 2})
        no_grace = QualitySpec.create(30, min_sales=100, protect_days=0, today=TODAY)
        self.assertEqual([x[0] for x in select_candidates(entries, no_grace)[0]], ["high"])
        self.assertEqual(QualitySpec.create(start="2026-10-01", end="2026-10-31", today=TODAY).end, date(2026, 10, 31))
        with self.assertRaises(ValueError):
            QualitySpec.create(start="2026-11-21", end="2026-11-22", today=TODAY)

    def test_catalog_uses_dates_and_detects_repeat(self):
        spec = QualitySpec.create(30, today=TODAY)
        first = [f"RJ{100000+i:06}" for i in range(100)]
        old = [f"RJ{200000+i:06}" for i in range(100)]
        page = lambda ids: "".join(f'<li data-list_item_product_id="{ident}"></li>' for ident in ids)
        fetcher = Mock()
        fetcher.get_text.side_effect = [page(first), page(old)]
        with patch("dlsite_tracker.quality_new.fetch_product_info", side_effect=lambda f, s, ids: {
            ident: info("2026-11-20" if ident in first else "2026-10-01", 200) for ident in ids
        }):
            entries, pages = collect_catalog(fetcher, "maniax", spec, lambda *_: None)
            self.assertEqual(pages, 2)
            self.assertEqual(len(select_candidates(entries, spec)[0]), 100)
        fetcher.get_text.side_effect = [page(first), page(first)]
        with patch("dlsite_tracker.quality_new.fetch_product_info", return_value={ident: info("2026-11-20", 200) for ident in first}):
            with self.assertRaisesRegex(ValueError, "重复"):
                collect_catalog(fetcher, "maniax", spec, lambda *_: None)

    def test_limit_existing_and_export_results(self):
        spec = QualitySpec.create(30, min_sales=100, max_works=2, today=TODAY)
        with tempfile.TemporaryDirectory() as tmp:
            cfg_file = Path(tmp) / "config.ini"
            cfg_file.write_text("[general]\n[images]\nenabled=false\n", encoding="utf-8")
            cfg = Config.load(cfg_file)
            store = Store(cfg.data_dir / "dlsite.sqlite")
            store.migrate()
            try:
                def row(ident):
                    return {"workno": ident, "site": "maniax", "age_category": 3, "work_type": "SOU", "product_name": "Synthetic"}
                store.upsert_work(row("RJ123456"))
                items = {"RJ123456": info("2026-11-20", 300), "RJ123457": info("2026-11-20", 200),
                         "RJ123458": info("2026-11-20", 150)}
                def enrich(f, st, config, ident, source):
                    result = row(ident)
                    st.upsert_work(result)
                    return result
                with patch("dlsite_tracker.quality_new.collect_catalog", return_value=(items, 1)), \
                     patch("dlsite_tracker.quality_new.enrich_one", side_effect=enrich) as enrich_mock:
                    result = run_quality_new(cfg, store, Mock(), spec, lambda *_: None)
                    self.assertEqual(enrich_mock.call_count, 1)
                self.assertEqual(result["matched"], 3)
                self.assertEqual(result["ids"], ["RJ123456", "RJ123457"])
                self.assertEqual((result["added"], result["already"]), (1, 1))
                export_current(cfg, store)
                exported = json.loads((cfg.out_dir / "works.json").read_text(encoding="utf-8"))
                self.assertEqual(exported["quality_new"]["ids"], result["ids"])
            finally:
                store.close()

    def test_age_profiles_are_independent(self):
        adult = SimpleNamespace(sites=["maniax"], default_work_types=["SOU"])
        general = SimpleNamespace(sites=["home"], default_work_types=["SOU"])
        adult_row = {"site": "maniax", "age_category": 3, "work_type": "SOU"}
        general_row = {"site": "home", "age_category": 1, "work_type": "SOU"}
        self.assertTrue(scope_allows(adult, adult_row))
        self.assertFalse(scope_allows(adult, general_row))
        self.assertFalse(scope_allows(general, adult_row))
        self.assertTrue(scope_allows(general, general_row))
        self.assertFalse(scope_allows(general, {**general_row, "age_category": 2}))
