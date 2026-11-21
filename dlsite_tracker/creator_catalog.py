"""按页读取 DLsite 官方搜索结果中的同人音声。"""

from __future__ import annotations

import json
import logging
import re
from html import unescape
from urllib.parse import urlencode

from .audio import edition_metadata, workno
from .http import HttpError
from .sales import SALES_API_URL

LOG = logging.getLogger(__name__)
PAGE_SIZE = 30
CIRCLE_ID = re.compile(r"RG[0-9]+")
WORK_ROW = re.compile(r'<li\b[^>]*\bdata-list_item_product_id="(RJ[0-9]+)"[^>]*>(.*?)</li>', re.S)
WORK_TYPE = re.compile(r'class="work_category\s+type_(\w+)')
ANCHOR = re.compile(r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>', re.S)
COVER = re.compile(r'//img\.dlsite\.jp/(?:resize|modpub)/images2/work/doujin/RJ\d+/RJ\d+_img_main_240x240\.(?:webp|jpe?g)')


def creator_url(site: str, kind: str, name: str, creator_id: str, page: int) -> str:
    if site not in ("maniax", "home") or kind not in ("voice", "circle"):
        raise ValueError("未知的音声目录范围")
    if not name.strip() or len(name) > 200 or page < 1:
        raise ValueError("声优或社团名称、页码无效")
    # 前端公开使用的 /fsr/ajax。这里省略语言选项，以查询所有语言。
    field = "keyword_creater" if kind == "voice" else "keyword_maker_name"
    name_or_id = creator_id if kind == "circle" and CIRCLE_ID.fullmatch(creator_id) else f'"{name.strip()}"'
    ages = ["general"] if site == "home" else ["r15", "adult"]
    params = {
        field: name_or_id, "work_type[0]": "SOU", "order[0]": "release_d",
        "age_category[]": ages, "page": page, "per_page": PAGE_SIZE, "show_type": 3,
    }
    return f"https://www.dlsite.com/{site}/fsr/ajax?{urlencode(params, doseq=True)}"


def _first_link(row: str, field: str):
    section = re.search(rf'<dd class="{field}">(.*?)</dd>', row, re.S)
    if section:
        return ANCHOR.search(section[1])
    return None


def _text(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", html)).strip()


def parse_creator_page(payload, site: str, kind: str, name: str, creator_id: str, page: int) -> dict:
    info = payload.get("page_info") if isinstance(payload, dict) else None
    html = payload.get("search_result") if isinstance(payload, dict) else None
    if not isinstance(info, dict) or not isinstance(html, str):
        raise ValueError("DLsite 未返回有效的作品列表")
    total, first, last = (info.get(key) for key in ("count", "first_indice", "last_indice"))
    if not all(type(value) is int and value >= 0 for value in (total, first, last)):
        raise ValueError("DLsite 的页码信息暂时无法读取")
    rows = WORK_ROW.findall(html)
    if total and (first != (page - 1) * PAGE_SIZE + 1 or not first <= last <= total
                  or len(rows) != last - first + 1):
        raise ValueError("DLsite 返回的页码或作品数量与本次请求不符")
    if not total and rows:
        raise ValueError("DLsite 返回了不一致的作品数量")

    works = {}
    for item_id, row in rows:
        matched_type = WORK_TYPE.search(row)
        if not matched_type:
            raise ValueError("DLsite 的作品分类暂时无法读取")
        if not workno(item_id) or matched_type[1] != "SOU":
            continue
        url = f"https://www.dlsite.com/{site}/work/=/product_id/{item_id}.html"
        title = _first_link(row, "work_name")
        maker = _first_link(row, "maker_name")
        if not title or title[1] != url or not _text(title[2]):
            raise ValueError("DLsite 的音声作品链接暂时无法读取")
        maker_name = _text(maker[2]) if maker else ""
        if kind == "circle":
            if not maker:
                raise ValueError("DLsite 的社团署名暂时无法读取")
            if CIRCLE_ID.fullmatch(creator_id):
                if not maker[1].endswith(f"/maker_id/{creator_id}.html"):
                    continue
            elif maker_name.casefold() != name.strip().casefold():
                continue
        cover = COVER.search(row)
        works[item_id] = {
            "id": item_id, "title": _text(title[2]), "maker": maker_name,
            "url": url, "cover": f"https:{cover[0]}" if cover else "",
        }
    return {"works": list(works.values()), "has_more": last < total}


def fetch_creator_page(fetcher, site: str, kind: str, name: str, creator_id: str, page: int, *, include_editions=False) -> dict:
    url = creator_url(site, kind, name, creator_id, page)
    try:
        payload = json.loads(fetcher.get_text(url, kind="page"))
    except json.JSONDecodeError as exc:
        raise ValueError("DLsite 暂时未返回搜索数据，请稍后重试") from exc
    result = parse_creator_page(payload, site, kind, name, creator_id, page)
    works = result["works"]
    if include_editions and works:
        ids = ",".join(work["id"] for work in works)
        try:
            products = fetcher.get_json(SALES_API_URL.format(site=site, ids=ids))
        except HttpError as exc:
            LOG.warning("读取在线目录的版本关系失败：%s", exc)
            return result
        if isinstance(products, dict):
            for work in works:
                item = products.get(work["id"])
                if isinstance(item, dict):
                    work.update(edition_metadata(item, work["id"]))
    return result
