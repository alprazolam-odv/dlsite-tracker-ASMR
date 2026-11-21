import type { Profile, Work } from "./api";
import { categoriesOf } from "./ui.ts";

export type Credit = { id: string; name: string };
export type ListenState = "want" | "heard" | "disliked";
export const LISTEN_LABELS: Record<ListenState, string> = { want: "想听", heard: "已听", disliked: "不喜欢" };

export function creditsOf(work: Work): Credit[] {
  if (work.voice_credits?.length) return work.voice_credits;
  return (work.voice_actors ?? "").split(" / ").filter(Boolean).map((name) => ({ id: "", name }));
}
export function creditKey(c: Credit): string { return c.id ? `id:${c.id}` : `name:${c.name}`; }
export function sameCredit(a: Credit, b: Credit): boolean {
  return a.id && b.id ? a.id === b.id : a.name === b.name;
}
export function hasCredit(work: Work, credit: Credit): boolean {
  return creditsOf(work).some((c) => sameCredit(c, credit));
}

export function dlsiteVoiceSearch(profile: Profile, name: string): string {
  const site = profile === "all-age" ? "home" : "maniax";
  return `https://www.dlsite.com/${site}/fsr/=/keyword_creater/${encodeURIComponent(`"${name}"`)}/work_type/SOU`;
}
export function actorDirectory<T extends Work>(works: T[]) {
  const map = new Map<string, { credit: Credit; count: number }>();
  const namedIds = new Map<string, Set<string>>();
  for (const work of works) for (const credit of creditsOf(work)) {
    if (!credit.id) continue;
    const ids = namedIds.get(credit.name) ?? new Set<string>();
    ids.add(credit.id);
    namedIds.set(credit.name, ids);
  }
  for (const work of works) {
    const seen = new Set<string>();
    for (let credit of creditsOf(work)) {
      const ids = namedIds.get(credit.name);
      if (!credit.id && ids?.size === 1) credit = { ...credit, id: [...ids][0] };
      const key = creditKey(credit);
      if (seen.has(key)) continue;
      seen.add(key);
      const old = map.get(key);
      map.set(key, { credit, count: (old?.count ?? 0) + 1 });
    }
  }
  return [...map.values()].sort((a, b) => b.count - a.count || a.credit.name.localeCompare(b.credit.name));
}

export const AUDIO_THEMES = [
  { name: "耳语与低语", regex: /耳语|低语|耳語|囁き|ささやき|whisper/i },
  { name: "采耳", regex: /采耳|掏耳|挖耳|耳かき|耳掃除|ear clean/i },
  { name: "双耳与空间录音", regex: /双耳|双声道|立体声|バイノーラル|binaural|dummy.head|环绕/i },
  { name: "助眠与放松", regex: /助眠|睡眠|安眠|催眠放松|放松|リラックス|睡前|sleep|relax/i },
  { name: "治愈陪伴", regex: /治愈|治癒|陪伴|癒し|安慰|陪睡|comfort/i },
  { name: "剧情与角色", regex: /剧情|故事|角色扮演|ドラマ|シチュエーション|roleplay|story/i },
  { name: "环境音与音效", regex: /环境音|音效|拟声|環境音|効果音|水音|rain|ambient|sound effects/i },
];
export function themesOf(work: Work): string[] {
  return AUDIO_THEMES.filter((t) => t.regex.test(work.category ?? "")).map((t) => t.name);
}
export function durationLabel(seconds?: number | null): string {
  if (!seconds || seconds <= 0) return "时长未知";
  const min = Math.round(seconds / 60);
  return min >= 60 ? `${Math.floor(min / 60)} 小时 ${min % 60} 分` : `${Math.max(1, min)} 分钟`;
}

export type EditionWork = Pick<Work, "id" | "original_id" | "related_ids">;

// 官方明确给出的作品关系才合并；不按相同标题或模糊相似度猜测。
export function editionGroups(works: EditionWork[], keyOf = (id: string) => id): Map<string, string[]> {
  const parent = new Map<string, string>();
  const root = (id: string): string => {
    let next = id;
    while (parent.has(next) && parent.get(next) !== next) next = parent.get(next)!;
    let node = id;
    while (parent.has(node) && parent.get(node) !== next) {
      const old = parent.get(node)!;
      parent.set(node, next);
      node = old;
    }
    return next;
  };
  for (const work of works) {
    const key = keyOf(work.id);
    if (!key) continue;
    if (!parent.has(key)) parent.set(key, key);
    for (const id of [work.original_id, ...(work.related_ids ?? [])]) {
      if (!id || !/^RJ\d{6}(?:\d{2})?$/.test(id)) continue;
      const related = keyOf(id);
      if (!related) continue;
      const a = root(key), b = root(related);
      if (a !== b) parent.set(b, a);
      if (!parent.has(a)) parent.set(a, a);
    }
  }
  const groups = new Map<string, string[]>();
  for (const id of parent.keys()) {
    const key = root(id), list = groups.get(key) ?? [];
    list.push(id); groups.set(key, list);
  }
  return new Map([...groups.values()].flatMap((ids) => ids.map((id) => [id, ids] as const)));
}
export function uniqueEditions<T extends Work>(works: T[], groups = editionGroups(works), preferOriginal = true): T[] {
  const originals = new Set(works.map((w) => w.original_id).filter(Boolean));
  const selected = new Map<string, T>();
  for (const w of works) {
    // 优先保留筛选范围内的原版；原版不符合条件时保留排序最靠前的可见译版。
    const group = (groups.get(w.id) ?? [w.id]).slice().sort()[0];
    const current = selected.get(group);
    if (!current || (preferOriginal && !originals.has(current.id) && originals.has(w.id))) selected.set(group, w);
  }
  const keep = new Set([...selected.values()].map((w) => w.id));
  return works.filter((w) => keep.has(w.id));
}
export function recent(work: Work, now = Date.now()): boolean {
  const date = Date.parse((work.regist_date ?? "").slice(0, 10) + "T00:00:00");
  return Number.isFinite(date) && date <= now && now - date < 14 * 86400_000;
}
export function recentTaggedWorks<T extends Work>(works: T[], names: readonly string[], now = Date.now()): T[] {
  const tags = new Set(names);
  if (!tags.size) return [];
  return works.filter((work) => recent(work, now) && categoriesOf(work).some((tag) => tags.has(tag)))
    .sort((a, b) => b.regist_date.localeCompare(a.regist_date) || b.id.localeCompare(a.id));
}
export function bedtimeReason(work: Work, minutes: number, taste: Record<string, string>, following: Credit[], allowUnknown = false): { score: number; reason: string } | null {
  if (!Number.isFinite(minutes) || minutes <= 0) return null;
  const tags = themesOf(work);
  const relax = tags.filter((tag) => ["助眠与放松", "耳语与低语", "治愈陪伴", "采耳", "环境音与音效"].includes(tag));
  const unknown = !work.duration_seconds || work.duration_seconds <= 0;
  if (!relax.length || (unknown ? !allowUnknown : work.duration_seconds! > minutes * 60)) return null;
  const raw = (work.category ?? "").split(/[、,，/|]+/).map((x) => x.trim());
  const liked = raw.filter((tag) => taste[tag] === "love" || taste[tag] === "like");
  if (raw.some((tag) => taste[tag] === "less")) return null;
  const follows = following.filter((credit) => hasCredit(work, credit));
  return {
    score: (unknown ? -1000 : 0) + relax.length * 3 + liked.length * 3 + follows.length * 4 + (work.rating_precise ?? work.rating ?? 0),
    reason: [...(unknown ? ["时长未知，备选"] : []), ...relax, ...follows.map((c) => `关注声优 ${c.name}`), ...liked].slice(0, 5).join(" · "),
  };
}
