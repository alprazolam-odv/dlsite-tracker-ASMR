import unittest
from urllib.parse import parse_qs, urlsplit

from dlsite_tracker.creator_catalog import creator_url, parse_creator_page


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
