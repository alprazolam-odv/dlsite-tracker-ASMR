"""按实际发售日期与公开销量筛选新音声；只富化命中的作品。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from .discovery import catalog_page_url, extract_catalog_items
from .http import HttpError
from .sales import fetch_product_info, save_product_info
from .enrich import enrich_one, scope_allows
from .images import download_covers
from .export import export_current

PAGE_SIZE = 100
RESULT_KEY = "quality_new_result"


@dataclass(frozen=True)
class QualitySpec:
    start: date
    end: date
    today: date
    min_sales: int = 100
    protect_days: int = 3
    max_works: int = 0

    @classmethod
    def create(cls, days=None, start=None, end=None, min_sales=100, protect_days=3, max_works=0, today=None):
        today = today or datetime.now(timezone(timedelta(hours=9))).date()
        if start is not None or end is not None:
            if not start or not end or days is not None:
                raise ValueError("请选择最近天数，或同时指定开始和结束日期")
            first, last = date.fromisoformat(start), date.fromisoformat(end)
        else:
            days = 30 if days is None else int(days)
            if not 1 <= days <= 36500:
                raise ValueError("最近天数须介于 1 和 36500 之间")
            first, last = today - timedelta(days=days - 1), today
        if first > last or last > today:
            raise ValueError("开始日期不得晚于结束日期，结束日期不得晚于今天")
        if min_sales < 0 or protect_days < 0 or protect_days > 36500 or max_works < 0:
            raise ValueError("最低销量、保护天数和数量上限必须为非负整数（0 表示关闭/不限）")
        return cls(first, last, today, int(min_sales), int(protect_days), int(max_works))


def release_date(info: Dict[str, Any]) -> Optional[date]:
    try:
        return date.fromisoformat(str(info.get("regist_date") or "")[:10])
    except ValueError:
        return None


def select_candidates(infos, spec: QualitySpec):
    """保留期间内达到门槛或受保护的 SOU，明确区分未知资料与低销量。"""
    selected = []
    stats = {"in_range": 0, "low_sales": 0, "unknown": 0, "protected": 0}
    for ident, info in infos.items():
        released = release_date(info)
        if released is None:
            stats["unknown"] += 1
            continue
        if not spec.start <= released <= spec.end:
            continue
        kind = info.get("work_type")
        if not kind:
            stats["unknown"] += 1
            continue
        if kind != "SOU":
            continue
        stats["in_range"] += 1
        sales = info.get("dl_count")
        protected = 0 <= (spec.today - released).days < spec.protect_days
        if spec.min_sales > 0 and (sales is None or sales < spec.min_sales):
            if not protected:
                stats["unknown" if sales is None else "low_sales"] += 1
                continue
            stats["protected"] += 1
        selected.append((ident, info, released, spec.min_sales > 0 and protected and (sales is None or sales < spec.min_sales)))
    selected.sort(key=lambda item: (item[1].get("dl_count") if item[1].get("dl_count") is not None else -1, item[2], item[0]), reverse=True)
    return selected, stats


def collect_catalog(fetcher, site: str, spec: QualitySpec, progress: Callable[[str, str], None]):
    """按官方发售日降序分页，批量核验日期、销量和类型，不以 RJ 编号猜测时间。"""
    infos = {}
    seen_pages = set()
    seen_ids = set()
    pages = 0
    page = 1
    while True:
        try:
            html = fetcher.get_text(catalog_page_url(site, "audio", page, PAGE_SIZE), kind="page")
        except HttpError as exc:
            if page > 1 and "HTTP 404" in str(exc):
                break
            raise
        worknos = extract_catalog_items(html)
        if not worknos:
            raise ValueError(f"音声目录第 {page} 页解析为空，未能确认采集范围")
        signature = frozenset(worknos)
        if signature in seen_pages:
            raise ValueError(f"音声目录第 {page} 页重复返回，停止以免错误声称覆盖完整范围")
        seen_pages.add(signature)
        unseen = [ident for ident in worknos if ident not in seen_ids]
        seen_ids.update(worknos)
        details = fetch_product_info(fetcher, site, unseen)
        for ident in unseen:
            infos[ident] = details.get(ident) or {}
        pages += 1
        # 页面内每件作品都具有真实日期且均早于起点时，已越过所需日期范围。
        dates = [release_date(infos.get(ident, {})) for ident in worknos]
        progress("rankings", f"优质新作：检查第 {page} 页 · 已核对 {len(seen_ids)} 部候选")
        if all(day is not None and day < spec.start for day in dates) or len(worknos) < PAGE_SIZE:
            break
        page += 1
    return infos, pages


def run_quality_new(cfg, store, fetcher, spec: QualitySpec, progress: Callable[[str, str], None]):
    # 此模式专门采集已配置的同人区音声，与全库和热榜数据并存。
    site = cfg.sites[0]
    info, pages = collect_catalog(fetcher, site, spec, progress)
    ranked, stats = select_candidates(info, spec)
    matched_total = len(ranked)
    selected = ranked[:spec.max_works] if spec.max_works else ranked
    existing = {row["workno"] for row in store.conn.execute(
        "SELECT workno,site,work_type,age_category FROM works WHERE enriched_at IS NOT NULL AND work_type='SOU'"
    ) if scope_allows(cfg, dict(row))}
    selected_ids = [item[0] for item in selected]
    if selected_ids:
        save_product_info(store, site, {ident: details for ident, details, _, _ in selected}, source="quality-new")
    added, already, failed, excluded = 0, 0, 0, 0
    success = []
    protected_ids = []
    for index, (ident, details, released, protected) in enumerate(selected, 1):
        if ident in existing:
            already += 1
            row_ok = True
        else:
            source = f"listing:{site}:quality-new"
            store.add_pending_many([ident], source)
            row = enrich_one(fetcher, store, cfg, ident, source)
            row_ok = bool(row and row.get("workno") == ident and scope_allows(cfg, row))
            if row_ok:
                added += 1
            elif row and not scope_allows(cfg, row):
                excluded += 1
            else:
                failed += 1
        if row_ok:
            success.append(ident)
            if protected:
                protected_ids.append(ident)
        if index % 10 == 0 or index == len(selected):
            progress("rankings", f"优质新作：收录 {index}/{len(selected)} · 新增 {added} · 已有 {already} · 失败 {failed}")
    result = {
        "start": spec.start.isoformat(), "end": spec.end.isoformat(),
        "min_sales": spec.min_sales, "protect_days": spec.protect_days,
        "max_works": spec.max_works, "scanned": len(info), "pages": pages,
        "in_range": stats["in_range"], "matched": matched_total,
        "low_sales": stats["low_sales"], "unknown": stats["unknown"],
        "added": added, "already": already, "failed": failed, "scope_excluded": excluded,
        "ids": success, "protected_ids": protected_ids,
        "protected": len(protected_ids),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    store.set_meta(RESULT_KEY, json.dumps(result, ensure_ascii=False))
    progress("export", "优质新作：导出筛选结果")
    export_current(cfg, store)
    if success:
        progress("images", "优质新作：补齐命中作品封面")
        covers = download_covers(cfg, fetcher, store, len(success), worknos=success,
            observer=lambda done, total: progress("images", f"优质新作：封面 {done}/{total}") if (done % 20 == 0 or done == total) else None)
        result["cover_failed"] = covers["failed"]
        store.set_meta(RESULT_KEY, json.dumps(result, ensure_ascii=False))
        export_current(cfg, store)
    return result
