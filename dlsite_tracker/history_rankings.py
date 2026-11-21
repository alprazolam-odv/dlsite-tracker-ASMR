"""只读浏览 DLsite 官方音声销量榜。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from html import unescape

from .discovery import RANKING_URL


RANK_ROW = re.compile(r'<div class="rank_no\b[^"]*">\s*(\d+)\s*</div>(.*?)</tr>', re.S)
RANK_SALES = re.compile(r'<div class="dl_count">\s*<span[^>]*>[^<]*</span>\s*([\d,]+)')
HEADING = re.compile(r'<h1\b[^>]*>([^<]+)</h1>')


def ranking_url(site: str, year: int | None) -> str:
    if site not in ("maniax", "home"):
        raise ValueError("历史佳作只支持成人区或全年龄同人区")
    current_year = datetime.now(timezone(timedelta(hours=9))).year
    if year is not None and not 2000 <= year <= current_year:
        raise ValueError(f"请选择 2000 至 {current_year} 年")
    term = "total" if year is None else "year"
    url = RANKING_URL.format(site=site, term=term, category="voice") + "&sub=SOU&sort=sale"
    return url if year is None else f"{url}&year={year}"


def extract_history_rankings(page: str, site: str, year: int | None) -> list[dict]:
    heading = HEADING.search(page)
    period = r"累[计計]" if year is None else rf"{year}\s*年"
    if not heading or "ASMR" not in heading[1] or not re.search(period, heading[1]):
        raise ValueError("DLsite 返回了其他榜单，无法确认当前音声榜")
    product = re.compile(
        rf'<a href="(https://www\.dlsite\.com/{site}/work/=/product_id/(RJ\d+)\.html)"[^>]*>(.*?)</a>',
        re.S,
    )
    results = []
    for rank, row in RANK_ROW.findall(page):
        if 'class="work_category type_SOU"' not in row:
            continue
        name = re.search(r'<dt class="work_name">(.*?)</dt>', row, re.S)
        work = product.search(name[1]) if name else None
        if not work:
            raise ValueError("DLsite 音声榜的作品链接无法解析")
        sales = RANK_SALES.search(row)
        maker = re.search(r'<dd class="maker_name">\s*<a\b[^>]*>([^<]*)</a>', row)
        released = re.search(r'<li class="sales_date">[^<]*?(\d{4})年(\d{2})月(\d{2})日', row)
        results.append({
            "id": work[2],
            "rank": int(rank),
            "url": work[1],
            "title": unescape(re.sub(r"<[^>]+>", "", work[3])).strip(),
            "maker": unescape(maker[1]).strip() if maker else "",
            "released": "-".join(released.groups()) if released else "",
            "sales": int(sales[1].replace(",", "")) if sales else None,
        })
    if not results and 'class="not_found_chara"' not in page:
        raise ValueError("DLsite 榜单暂时无法解析")
    return results


def fetch_history_rankings(fetcher, site: str, year: int | None) -> dict:
    url = ranking_url(site, year)
    page = fetcher.get_text(url, kind="page")
    return {"works": extract_history_rankings(page, site, year)}
