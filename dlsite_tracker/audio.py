"""音声元数据：只使用公开作品资料中的明示字段。"""

from __future__ import annotations

import html
import json
import re
from typing import Any, Dict, Optional

from .sales import LANGUAGE_TOKENS, parse_options

WORKNO = re.compile(r"RJ(?:\d{8}|\d{6})", re.I)
LANGUAGE_NAMES = {
    "JPN": "日语", "ENG": "英语", "CHI": "中文", "CHI_HANS": "简体中文",
    "CHI_HANT": "繁体中文", "KO_KR": "韩语",
    "ja": "日语", "en": "英语", "zh": "中文", "zh_CN": "简体中文",
    "zh_TW": "繁体中文", "ko": "韩语",
}


def workno(value: Any) -> Optional[str]:
    if isinstance(value, str) and WORKNO.fullmatch(value):
        return value.upper()
    return None


def audio_metadata(item: Dict[str, Any]) -> Dict[str, Any]:
    creators = item.get("creaters")
    raw = creators.get("voice_by") if isinstance(creators, dict) else None
    actors = []
    if isinstance(raw, list):
        for credit in raw:
            if not isinstance(credit, dict) or not isinstance(credit.get("name"), str):
                continue
            name = credit["name"].strip()
            actor_id = str(credit.get("id") or "")
            if name and not any(a["name"] == name and a["id"] == actor_id for a in actors):
                actors.append({"id": actor_id, "name": name})
    if not actors and isinstance(item.get("voice_by"), str) and item["voice_by"].strip():
        actors.append({"id": "", "name": item["voice_by"].strip()})
    options = parse_options(item.get("work_attributes")).split("#")
    languages = [LANGUAGE_NAMES[t] for t in options if t in LANGUAGE_TOKENS]
    translation = item.get("translation_info")
    translation = translation if isinstance(translation, dict) else {}
    language = translation.get("lang")
    if isinstance(language, str) and language in LANGUAGE_NAMES:
        languages.append(LANGUAGE_NAMES[language])
    original = workno(translation.get("original_workno")) or workno(translation.get("parent_workno"))
    current = workno(item.get("workno"))
    if original == current:
        original = None
    related = []
    children = translation.get("child_worknos")
    for entry in children if isinstance(children, list) else []:
        ident = workno(entry)
        if ident and ident != current:
            related.append(ident)
    for field in ("language_editions", "editions"):
        editions = item.get(field)
        for entry in editions if isinstance(editions, list) else []:
            ident = workno(entry if isinstance(entry, str) else entry.get("workno") if isinstance(entry, dict) else None)
            if ident and ident != current:
                related.append(ident)
    if original:
        related.append(original)
    return {
        "voice_credits": actors,
        "languages": list(dict.fromkeys(languages)),
        "original_id": original,
        "related_ids": list(dict.fromkeys(related)),
        "has_preview": bool(item.get("trials") or "TRI" in options or item.get("is_viewable_sample")),
    }


# 仅识别「总时长」这样的明确标签；单轨时长、未注明时长、冲突数字都不猜测。
TOTAL_LABEL = re.compile(
    r"(?:本編\s*)?(?:総(?:再生|収録|演奏|音声)?時間|合計(?:再生|収録)?時間|"
    r"全(?:編|体)(?:の)?(?:再生|収録)時間|总(?:播放|收录|录音|音频)?时长|"
    r"總(?:播放|收錄|錄音|音頻)?時長|total\s+(?:play(?:back)?\s+time|duration|running\s+time))"
    r"\s*[:：：=約约約・\s]*",
    re.I,
)
UNITS = re.compile(
    r"(?:(\d+)\s*(?:時間|小时|小時|hours?|hrs?|h)\s*)?"
    r"(?:(\d+)\s*(?:分(?:鐘|钟)?|minutes?|mins?|m)\s*)?"
    r"(?:(\d+)\s*(?:秒|seconds?|secs?|s))?",
    re.I,
)


def explicit_duration_seconds(value: Any) -> Optional[int]:
    if not isinstance(value, str):
        return None
    value = html.unescape(re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", value, flags=re.I | re.S))
    value = re.sub(r"<[^>]+>", " ", value)
    # 全角数字也属于原文，不改变时长语义。
    found = set()
    for label in TOTAL_LABEL.finditer(value):
        after = value[label.end(): label.end() + 80]
        clock = re.match(r"(\d{1,3}):(\d{2}):(\d{2})(?!\d)", after)
        if clock:
            h, m, s = map(int, clock.groups())
            if m < 60 and s < 60:
                found.add(h * 3600 + m * 60 + s)
            continue
        match = UNITS.match(after)
        if match and any(match.groups()):
            h, m, s = (int(part or 0) for part in match.groups())
            found.add(h * 3600 + m * 60 + s)
    valid = [seconds for seconds in found if 0 < seconds <= 100 * 3600]
    return valid[0] if len(valid) == 1 and len(found) == 1 else None


def metadata_json(item: Dict[str, Any]) -> str:
    return json.dumps(audio_metadata(item), ensure_ascii=False)
