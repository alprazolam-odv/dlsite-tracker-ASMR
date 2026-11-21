import json
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

from dlsite_tracker.creator_catalog import creator_url, fetch_creator_page, parse_creator_page
from dlsite_tracker.http import HttpError


def search_row(id, maker_id="RG101", work_type="SOU", site="home"):
    return f'''
<li data-list_item_product_id="{id}">
  <dl><dt><thumb-with-ng-filter-block :thumb-candidates="['//img.dlsite.jp/resize/images2/work/doujin/RJ124000/RJ123454_img_main_240x240.webp']"></thumb-with-ng-filter-block></dt>
    <dd><div class="work_category type_{work_type}">分类</div></dd>
    <dd class="work_name"><a href="https://www.dlsite.com/{site}/work/=/product_id/{id}.html">音声 &amp; ASMR</a></dd>
    <dd class="maker_name"><a href="https://www.dlsite.com/{site}/circle/profile/=/maker_id/{maker_id}.html">社团</a></dd>
  </dl>
</li>
'''


class CreatorCatalogTest(unittest.TestCase):
    def test_official_search_is_paged_sound_only_and_has_no_language_filter(self):
        urls = [
            creator_url("maniax", "voice", "名字 & 名前", "", 2),
            creator_url("home", "circle", "&MORE", "RG63213", 3),
        ]
        paths = [urlsplit(url) for url in urls]
        self.assertEqual([url.path for url in paths], ["/maniax/fsr/ajax", "/home/fsr/ajax"])
        voice, circle = [parse_qs(url.query) for url in paths]
        self.assertEqual(voice["keyword_creater"], ['"名字 & 名前"'])
        self.assertEqual(voice["age_category[]"], ["r15", "adult"])
        self.assertEqual(voice["page"], ["2"])
        self.assertEqual(circle["keyword_maker_name"], ["RG63213"])
        self.assertEqual(circle["age_category[]"], ["general"])
        for params in (voice, circle):
            self.assertEqual(params["work_type[0]"], ["SOU"])
            self.assertFalse(any(key.startswith("options") for key in params))

    def test_filtered_rows_preserve_pagination_and_translation_cover(self):
        data = {
            "page_info": {"count": 33, "first_indice": 31, "last_indice": 32},
            "search_result": search_row("RJ123456") + search_row("RJ123457", maker_id="RG102"),
        }
        page = parse_creator_page(data, "home", "circle", "社团", "RG101", 2)
        self.assertTrue(page["has_more"])
        self.assertEqual([work["id"] for work in page["works"]], ["RJ123456"])
        self.assertEqual(page["works"][0]["title"], "音声 & ASMR")
        self.assertIn("RJ123454_img_main", page["works"][0]["cover"])
        data["search_result"] = search_row("RJ123456") + search_row("RJ123457", work_type="MUS")
        self.assertEqual(len(parse_creator_page(data, "home", "voice", "演员", "", 2)["works"]), 1)
        with self.assertRaises(ValueError):
            parse_creator_page(data, "home", "voice", "演员", "", 3)

    def test_zero_results_is_distinct_from_invalid_payload(self):
        empty = {"page_info": {"count": 0, "first_indice": 1, "last_indice": 0}, "search_result": ""}
        self.assertEqual(parse_creator_page(empty, "home", "voice", "演员", "", 1),
                         {"works": [], "has_more": False})
        with self.assertRaises(ValueError):
            parse_creator_page([], "home", "voice", "演员", "", 1)

    def test_online_catalog_adds_official_edition_links_with_one_product_request(self):
        fetcher = Mock()
        fetcher.get_text.return_value = json.dumps({
            "page_info": {"count": 2, "first_indice": 1, "last_indice": 2},
            "search_result": search_row("RJ123456") + search_row("RJ123457"),
        })
        fetcher.get_json.return_value = {"RJ123456": {
            "translation_info": {"original_workno": "RJ123454", "child_worknos": ["RJ123458"]},
        }}
        args = (fetcher, "home", "voice", "演员", "", 1)
        self.assertNotIn("original_id", fetch_creator_page(*args)["works"][0])
        fetcher.get_json.assert_not_called()
        works = fetch_creator_page(*args, include_editions=True)["works"]
        self.assertEqual(works[0]["original_id"], "RJ123454")
        self.assertEqual(works[0]["related_ids"], ["RJ123458", "RJ123454"])
        self.assertNotIn("original_id", works[1])
        fetcher.get_json.assert_called_once()
        url = fetcher.get_json.call_args.args[0]
        self.assertEqual(parse_qs(urlsplit(url).query)["product_id"], ["RJ123456,RJ123457"])

        fetcher.get_json.side_effect = HttpError("offline")
        with self.assertLogs("dlsite_tracker.creator_catalog", level="WARNING"):
            fallback = fetch_creator_page(*args, include_editions=True)
        self.assertEqual([work["id"] for work in fallback["works"]], ["RJ123456", "RJ123457"])
        self.assertNotIn("original_id", fallback["works"][0])
