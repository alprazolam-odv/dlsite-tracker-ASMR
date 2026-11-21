import unittest

from dlsite_tracker.history_rankings import extract_history_rankings, ranking_url


def rank_row(rank, work_type, workno):
    return f'''
    <tr>
      <td><div class="rank_no type_{rank}">{rank}</div>
        <div class="dl_count"><span class="dl_count_label">售出数</span>1,234</div>
      </td>
      <td><div class="work_category type_{work_type}">分类</div></td>
      <td><dl>
        <dt class="work_name">
          <div class="icon_wrap"><span>专卖</span></div>
          <a href="https://www.dlsite.com/maniax/work/=/product_id/{workno}.html">声音 &amp; 睡眠</a>
        </dt>
        <dd class="maker_name"><a href="https://www.dlsite.com/maniax/circle/">社团</a></dd>
      </dl></td>
      <td><ul><li class="sales_date">发售日:&nbsp;2023年08月07日</li>
         <li><span class="_dl_count_{workno}">5,432</span></li>
      </ul></td>
    </tr>
    '''


class HistoryRankingsTest(unittest.TestCase):
    def test_sales_use_rank_period_and_keep_older_audio_at_official_rank(self):
        page = '<h1>同人 音声・ASMR排行榜 (2025年)</h1>'
        page += rank_row(1, "MUS", "RJ123456") + rank_row(2, "SOU", "RJ123457")
        self.assertEqual(extract_history_rankings(page, "maniax", 2025), [{
            "id": "RJ123457", "rank": 2, "sales": 1234,
            "title": "声音 & 睡眠", "maker": "社团", "released": "2023-08-07",
            "url": "https://www.dlsite.com/maniax/work/=/product_id/RJ123457.html",
        }])

    def test_recognized_empty_year_is_distinct_from_wrong_or_changed_page(self):
        page = '<h1>同人 音声・ASMR排行榜 (2000年)</h1>'
        self.assertEqual(extract_history_rankings(page + '<div class="not_found_chara">空</div>', "home", 2000), [])
        with self.assertRaises(ValueError):
            extract_history_rankings(page, "home", 2000)
        with self.assertRaises(ValueError):
            extract_history_rankings(page, "home", 2001)

    def test_tied_ranks_preserve_both_works(self):
        page = '<h1>同人 音声・ASMR排行榜 (累计)</h1>'
        page += rank_row(1, "SOU", "RJ123456") + rank_row(1, "SOU", "RJ123457")
        works = extract_history_rankings(page, "maniax", None)
        self.assertEqual([(work["id"], work["rank"]) for work in works], [
            ("RJ123456", 1), ("RJ123457", 1),
        ])

    def test_total_and_year_use_official_voice_sales_filters(self):
        self.assertIn("/home/ranking/total?category=voice", ranking_url("home", None))
        self.assertTrue(ranking_url("maniax", 2025).endswith("&sub=SOU&sort=sale&year=2025"))
