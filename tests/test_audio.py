import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dlsite_tracker.audio import audio_metadata, explicit_duration_seconds
from dlsite_tracker.enrich import parse_product
from dlsite_tracker.export import fetch_records
from dlsite_tracker.store import Store
from dlsite_tracker.cli import cmd_audio_details
from dlsite_tracker.config import Config


class AudioMetadataTest(unittest.TestCase):
    def test_official_fields_exported(self):
        item = {
            "workno": "RJ12345678", "work_name": "Synthetic audio", "work_type": "SOU",
            "work_attributes": "SOU,JPN,CHI_HANS,TRI",
            "creaters": {"voice_by": [{"id": "1", "name": "Voice A"}, {"id": "2", "name": "Voice B"}]},
            "translation_info": {"original_workno": "RJ123456", "lang": "zh_CN"},
            "language_editions": [{"workno": "RJ12345679"}],
            "intro": "本編総再生時間：1時間30分",
        }
        meta = audio_metadata(item)
        self.assertEqual(meta["languages"], ["日语", "简体中文"])
        self.assertEqual(meta["original_id"], "RJ123456")
        self.assertEqual(meta["related_ids"], ["RJ12345679", "RJ123456"])
        self.assertTrue(meta["has_preview"])
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "test.sqlite")
            store.migrate()
            try:
                row, genres = parse_product([item], item["workno"])
                self.assertEqual(json.loads(row["audio_meta"])["voice_credits"], meta["voice_credits"])
                store.upsert_work(row)
                store.replace_genres(item["workno"], genres)
                result = fetch_records(store, Path(tmp), work_types=["SOU"])[0]
                self.assertEqual(result["voice_credits"], meta["voice_credits"])
                self.assertEqual(result["languages"], meta["languages"])
                self.assertEqual(result["duration_seconds"], 5400)
            finally:
                store.close()

    def test_missing_or_conflicting_duration_is_not_guessed(self):
        self.assertIsNone(explicit_duration_seconds("Track 1: 30分 Track 2: 20分"))
        self.assertIsNone(explicit_duration_seconds("総再生時間 30分　総再生時間 50分"))
        self.assertIsNone(explicit_duration_seconds("<script>総再生時間 30分</script>"))
        self.assertEqual(explicit_duration_seconds("<b>本編総再生時間</b>　5時間0分<br>"), 18000)
        self.assertEqual(explicit_duration_seconds("总时长：01:30:05"), 5405)

    def test_offline_export_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.ini"
            config.write_text("[general]\n", encoding="utf-8")
            cfg = Config.load(config)
            cfg.out_dir.mkdir(parents=True)
            export = cfg.out_dir / "works.json"
            export.write_text("existing export", encoding="utf-8")
            self.assertEqual(cmd_audio_details(cfg, SimpleNamespace(limit=10, workno=None)), 1)
            self.assertEqual(export.read_text(encoding="utf-8"), "existing export")

    def test_details_updates_existing_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.ini"
            config.write_text("[general]\n", encoding="utf-8")
            cfg = Config.load(config)
            store = Store(cfg.data_dir / "dlsite.sqlite")
            store.migrate()
            store.upsert_work({"workno": "RJ123456", "site": "maniax", "work_type": "SOU", "product_name": "Synthetic"})
            store.close()
            fetcher = Mock()
            fetcher.get_json.return_value = [{
                "workno": "RJ123456", "site_id": "maniax", "work_name": "Synthetic", "work_type": "SOU",
                "work_attributes": "SOU,JPN",
                "creaters": {"voice_by": [{"id": "1", "name": "Voice A"}]},
            }]
            fetcher.get_text.return_value = "<html>RJ123456<br>総再生時間 40分</html>"
            with patch("dlsite_tracker.cli._fetcher", return_value=fetcher):
                self.assertEqual(cmd_audio_details(cfg, SimpleNamespace(limit=10, workno="RJ123456")), 0)
            data = json.loads((cfg.out_dir / "works.json").read_text(encoding="utf-8"))
            result = data["works"][0]
            self.assertEqual(result["duration_seconds"], 2400)
            self.assertEqual(result["voice_credits"], [{"id": "1", "name": "Voice A"}])
