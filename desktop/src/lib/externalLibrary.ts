import { writable } from "svelte/store";

type Profile = "adult" | "all-age";
type Lookup = (endpoint: string, ids: string[], signal: AbortSignal, snapshot?: string) => Promise<unknown>;
export type LibraryMarks = { collected: Set<string>; excluded: Set<string>; unknown: Set<string> };

const emptyMarks = (): LibraryMarks => ({ collected: new Set(), excluded: new Set(), unknown: new Set() });
const defaults = () => ({
  endpoint: "", hideCollected: false, hideExcluded: false,
  marks: emptyMarks(), syncedAt: 0, partial: false, syncing: false, error: "", storageError: "",
});

export function libraryKey(raw: string) {
  return typeof raw === "string" ? /^RJ0*([1-9][0-9]*)$/i.exec(raw.trim())?.[1] ?? "" : "";
}

export function libraryEndpoint(value: string) {
  if (!value.trim()) return "";
  try {
    const url = new URL(value.trim());
    if (["http:", "https:"].includes(url.protocol) && !url.username && !url.password && !url.hash) return url.href;
  } catch { /* Report the same validation message for malformed URLs. */ }
  throw new Error("请输入完整的 HTTP 或 HTTPS 接口地址。");
}

const fetchLookup: Lookup = async (endpoint, rjs, signal, snapshot) => {
  const response = await fetch(endpoint, {
    method: "POST", headers: { "Content-Type": "application/json" },
    credentials: "omit", redirect: "error", cache: "no-store", signal,
    body: JSON.stringify({ action: "check_library", rjs, snapshot }),
  });
  if (!response.ok) throw new Error(`接口返回 HTTP ${response.status}`);
  return response.json();
};

function readBatch(raw: unknown, ids: string[]) {
  const data = raw as Record<string, unknown> | null;
  if (!data || data.ok === false || typeof data.complete !== "boolean"
      || !["collected", "excluded", "absent", "unknown"].every((key) => Array.isArray(data[key]))) {
    throw new Error("接口缺少明确的作品状态，请检查接口地址和服务版本");
  }
  const requested = new Set(ids.map(libraryKey));
  function group(values: unknown[]) {
    const result = new Set<string>();
    for (const value of values) {
      const key = typeof value === "string" ? libraryKey(value) : "";
      if (!requested.has(key)) throw new Error("接口返回了本批次以外的 RJ 编号");
      result.add(key);
    }
    return result;
  }
  const collected = group(data.collected as unknown[]), absent = group(data.absent as unknown[]), unknown = group(data.unknown as unknown[]);
  const excluded = group(data.excluded as unknown[]);
  for (const key of requested) {
    if (Number(collected.has(key)) + Number(absent.has(key)) + Number(unknown.has(key)) !== 1) {
      throw new Error("接口返回的收录状态有遗漏或冲突");
    }
  }
  if (data.complete && unknown.size) throw new Error("接口同时报告查询完整和未知作品");
  return { collected, excluded, unknown, complete: data.complete,
    snapshot: typeof data.snapshot === "string" ? data.snapshot : undefined };
}

type LibraryState = ReturnType<typeof defaults>;

export function visibleLibraryWorks<T extends { id: string }>(works: T[], state: LibraryState): T[] {
  if (!state.endpoint || (!state.hideCollected && !state.hideExcluded)) return works;
  return works.filter(({ id }) => {
    const key = libraryKey(id);
    return !(state.hideCollected && state.marks.collected.has(key) || state.hideExcluded && state.marks.excluded.has(key));
  });
}

export function createExternalLibrary(lookup: Lookup = fetchLookup, storage = () => localStorage) {
  let state = defaults();
  const store = writable(state);
  let storageKey = "";
  let catalog: { id: string }[] = [];
  let requested = new Map<string, string>();
  let active: AbortController | undefined;

  function update(changes: Partial<LibraryState>) {
    state = { ...state, ...changes };
    store.set(state);
  }

  function persist() {
    if (!storageKey) return;
    try {
      if (state.endpoint) {
        const { endpoint, syncedAt, partial, hideCollected, hideExcluded, marks } = state;
        storage().setItem(storageKey, JSON.stringify({
          endpoint, syncedAt, partial, hideCollected, hideExcluded,
          collected: [...marks.collected], excluded: [...marks.excluded], unknown: [...marks.unknown],
        }));
      } else {
        storage().removeItem(storageKey);
      }
      if (state.storageError) update({ storageError: "" });
    } catch {
      update({ storageError: "无法保存外部作品库设置或标记，下次启动可能恢复到上一次保存的状态。" });
    }
  }

  function useProfile(profile: Profile) {
    active?.abort();
    active = undefined;
    catalog = [];
    requested = new Map();
    storageKey = `radar.externalLibrary.v1.${profile}`;
    update(defaults());
    try {
      const saved = JSON.parse(storage().getItem(storageKey) ?? "null");
      if (!saved?.endpoint) return;
      const marks = emptyMarks();
      for (const name of ["collected", "excluded", "unknown"] as const) {
        for (const key of saved[name]) {
          if (typeof key === "string" && /^[1-9][0-9]*$/.test(key)) marks[name].add(key);
        }
      }
      update({ endpoint: libraryEndpoint(saved.endpoint), hideCollected: saved.hideCollected === true,
        hideExcluded: saved.hideExcluded === true, syncedAt: Number(saved.syncedAt) || 0,
        partial: saved.partial === true, marks });
    } catch { /* A damaged or unavailable optional cache must not block startup. */ }
  }

  async function refresh() {
    active?.abort();
    active = undefined;
    const { endpoint, marks: previous } = state;
    if (!endpoint || !requested.size) { update({ syncing: false }); return; }
    const controller = new AbortController();
    active = controller;
    update({ syncing: true, error: "" });
    const ids = [...requested.values()];
    const marks = emptyMarks();
    let partial = false;
    let snapshot: string | undefined;
    try {
      for (let offset = 0; offset < ids.length; offset += 5000) {
        const batch = ids.slice(offset, offset + 5000);
        const timer = setTimeout(() => controller.abort(), 120_000);
        try {
          const raw = await lookup(endpoint, batch, controller.signal, snapshot);
          if (active !== controller) return;
          const result = readBatch(raw, batch);
          snapshot = result.snapshot;
          partial ||= !result.complete;
          for (const key of result.collected) marks.collected.add(key);
          for (const key of result.excluded) marks.excluded.add(key);
          for (const key of result.unknown) {
            marks.unknown.add(key);
            if (previous.collected.has(key)) marks.collected.add(key);
          }
        } finally { clearTimeout(timer); }
      }
      update({ marks, partial, syncedAt: Date.now() });
      persist();
    } catch (error) {
      if (active === controller) {
        const reason = controller.signal.aborted ? "查询超时" :
          error instanceof TypeError ? "无法连接接口，请检查服务地址或跨域设置" : String(error).replace(/^Error: /, "");
        update({ error: reason });
      }
    } finally {
      if (active === controller) { active = undefined; update({ syncing: false }); }
    }
  }

  function setWorks(works: { id: string }[]) {
    catalog = works;
    if (!state.endpoint) return;
    const next = new Map<string, string>();
    for (const { id } of works) {
      const key = libraryKey(id);
      if (key && !next.has(key)) next.set(key, id.trim().toUpperCase());
    }
    if (next.size === requested.size && [...next.keys()].every((key) => requested.has(key))) return;
    requested = next;
    return refresh();
  }

  function configure(address: string) {
    const endpoint = libraryEndpoint(address);
    if (endpoint === state.endpoint) return;
    active?.abort();
    active = undefined;
    requested = new Map();
    update({ ...defaults(), endpoint });
    persist();
    return setWorks(catalog);
  }

  function setFilter(name: "hideCollected" | "hideExcluded", value: boolean) {
    update({ [name]: value });
    persist();
  }

  async function lookupPage(ids: string[], signal: AbortSignal): Promise<LibraryMarks> {
    const { endpoint, marks: previous } = state;
    const lookupIds = [...new Map(ids.filter(id => libraryKey(id)).map(id => [libraryKey(id), id])).values()];
    if (!endpoint || !lookupIds.length) return emptyMarks();
    const result = readBatch(await lookup(endpoint, lookupIds, signal), lookupIds);
    for (const key of result.unknown) {
      if (previous.collected.has(key)) result.collected.add(key);
    }
    return result;
  }

  return { subscribe: store.subscribe, useProfile, configure, setWorks, setFilter, refresh, lookupPage };
}

export const externalLibrary = createExternalLibrary();
