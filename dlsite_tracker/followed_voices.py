"""补齐已关注声优的目录，并从最新页增量发现作品。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from .creator_catalog import fetch_creator_page
from .enrich import PRODUCT_API_URL, parse_product, scope_allows
from .export import export_current
from .http import HttpError
from .images import download_entries
from .sales import sync_sales

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Voice:
    id: str
    name: str

    def matches(self, credit: dict) -> bool:
        if self.id and credit.get("id"):
            return self.id == credit["id"]
        return self.name == credit.get("name")

    def state_key(self, site: str) -> str:
        return f"followed-voice:{site}:" + json.dumps([self.id, self.name], ensure_ascii=False)


def load_follows(path: Path) -> list[Voice]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(dict.fromkeys(Voice(item["id"], item["name"]) for item in data))


@dataclass
class CatalogState:
    complete: bool = False
    known: set[str] = field(default_factory=set)
    pending: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, store, key: str) -> CatalogState:
        state = json.loads(store.get_meta(key) or "{}")
        return cls(state.get("complete", False), set(state.get("known", [])), set(state.get("pending", [])))

    def save(self, store, key: str) -> None:
        store.set_meta(key, json.dumps({
            "complete": self.complete, "known": sorted(self.known), "pending": sorted(self.pending),
        }))


class FollowedVoiceSync:
    def __init__(self, cfg, store, fetcher, follows_file: Path, progress):
        self.cfg = cfg
        self.site = cfg.sites[0]
        self.store = store
        self.fetcher = fetcher
        self.follows_file = follows_file
        self.progress = progress
        self.products = {}
        self.added = 0
        self.failed_voices = 0

    def followed(self, voice: Voice) -> bool:
        return voice in load_follows(self.follows_file)

    def product(self, ident: str):
        local = self.store.conn.execute(
            "SELECT site, work_type, age_category, audio_meta FROM works "
            "WHERE workno=? AND enriched_at IS NOT NULL AND audio_meta IS NOT NULL", (ident,),
        ).fetchone()
        if local is not None:
            return dict(local), None
        if ident not in self.products:
            url = PRODUCT_API_URL.format(site=self.site, workno=ident, locale=self.cfg.locale)
            parsed = parse_product(self.fetcher.get_json(url), ident)
            if not parsed or parsed[0]["workno"] != ident:
                raise ValueError(f"DLsite 未返回 {ident} 的作品资料")
            self.products[ident] = parsed
        return self.products[ident]

    def process_batch(self, voice: Voice, state: CatalogState, identifiers: list[str]) -> bool:
        added = []
        covers = []
        cancelled = False
        for ident in identifiers:
            if not self.followed(voice):
                cancelled = True
                break
            try:
                row, genres = self.product(ident)
            except (HttpError, ValueError) as exc:
                LOG.warning("%s · %s 资料暂未补齐：%s", voice.name, ident, exc)
                state.pending.add(ident)
                continue
            if not self.followed(voice):
                cancelled = True
                break
            credits = json.loads(row["audio_meta"])["voice_credits"]
            if scope_allows(self.cfg, row) and any(voice.matches(credit) for credit in credits) and genres is not None:
                self.store.save_enriched_work(ident, row, genres)
                self.added += 1
                added.append(ident)
                if row.get("image_url"):
                    covers.append((ident, row["image_url"]))
            state.known.add(ident)
            state.pending.discard(ident)
        if added:
            try:
                sync_sales(self.fetcher, self.store, self.cfg, added)
            except (HttpError, ValueError) as exc:
                LOG.warning("关注声优作品销量补记失败：%s", exc)
            download_entries(self.cfg, self.fetcher, covers)
        if identifiers:
            # 导出后再推进目录记录。若中途退出，下一次会重读该页并跳过已保存的资料。
            export_current(self.cfg, self.store)
        state.save(self.store, voice.state_key(self.site))
        return not cancelled

    def scan(self, voice: Voice, state: CatalogState, check: bool) -> None:
        pending = sorted(state.pending)
        if pending and not self.process_batch(voice, state, pending):
            return
        if state.complete and not check:
            return

        previous = state.known | state.pending if state.complete else set()
        attempted = set(pending)
        pages = set()
        page = 1
        while self.followed(voice):
            action = "检查新作" if state.complete else "补齐历史作品"
            self.progress(f"关注声优 · {voice.name} · {action}第 {page} 页 · 已入库 {self.added} 部")
            result = fetch_creator_page(self.fetcher, self.site, "voice", voice.name, voice.id, page)
            ids = tuple(work["id"] for work in result["works"])
            if ids and ids in pages:
                raise ValueError(f"{voice.name} 第 {page} 页重复返回，请稍后重试")
            pages.add(ids)

            new_ids = [ident for ident in ids if ident not in state.known and ident not in attempted]
            attempted.update(new_ids)
            if new_ids and not self.process_batch(voice, state, new_ids):
                return
            if not result["has_more"] or (ids and all(ident in previous for ident in ids)):
                state.complete = True
                state.save(self.store, voice.state_key(self.site))
                return
            page += 1

    def run(self, check: bool) -> dict:
        jobs = [(voice, CatalogState.load(self.store, voice.state_key(self.site)))
                for voice in load_follows(self.follows_file)]
        jobs = [(voice, state) for voice, state in jobs if check or not state.complete or state.pending]
        if jobs:
            self.progress("正在同步关注声优的作品目录…")
            self.fetcher.verify_robots()
        for voice, state in jobs:
            if not self.followed(voice):
                continue
            try:
                self.scan(voice, state, check)
            except (HttpError, ValueError) as exc:
                LOG.warning("读取 %s 的作品目录失败：%s", voice.name, exc)
                self.failed_voices += 1
        pending = sum(len(state.pending) for voice, state in jobs if self.followed(voice))
        return {"checked": len(jobs), "added": self.added, "failed_voices": self.failed_voices, "pending": pending}
