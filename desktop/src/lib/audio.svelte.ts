import { type Credit, type ListenState, hasCredit, sameCredit, recent } from "./audio";
import type { Work } from "./api";

type AudioPreferences = {
  following: Credit[];
  listening: Record<string, ListenState>;
  localIds: string[];
  acknowledged: string[];
};
const KEY = "radar.audio.v1";
let storageKey = KEY;
function load(): AudioPreferences {
  const defaults: AudioPreferences = { following: [], listening: {}, localIds: [], acknowledged: [] };
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) ?? "{}");
    return { ...defaults, ...parsed };
  } catch { return defaults; }
}
class AudioStore {
  data = $state<AudioPreferences>(load());
  useProfile(profile: "adult" | "all-age") {
    storageKey = profile === "all-age" ? KEY + ".all-age" : KEY;
    this.data = load();
  }
  persist() { try { localStorage.setItem(storageKey, JSON.stringify(this.data)); } catch { /* local storage unavailable */ } }
  isFollowing(credit: Credit) { return this.data.following.some((c) => sameCredit(c, credit)); }
  toggle(credit: Credit) {
    if (this.isFollowing(credit)) this.data.following = this.data.following.filter((c) => !sameCredit(c, credit));
    else this.data.following = [...this.data.following, credit];
    this.persist();
  }
  setListening(id: string, state: ListenState | "") {
    if (state) this.data.listening[id] = state;
    else delete this.data.listening[id];
    this.persist();
  }
  setLocalIds(ids: string[]) { this.data.localIds = [...new Set(ids)]; this.persist(); }
  recentFollowed<T extends Work>(works: T[]): T[] {
    return works.filter((work) =>
      recent(work) && this.data.following.some((credit) => hasCredit(work, credit)));
  }
  unread<T extends Work>(followedWorks: T[]): T[] {
    const seen = new Set(this.data.acknowledged);
    return followedWorks.filter((work) => !seen.has(work.id));
  }
  acknowledge(workIds: string[]) {
    this.data.acknowledged = [...new Set([...this.data.acknowledged, ...workIds])].slice(-10000);
    this.persist();
  }
}
export const audioLibrary = new AudioStore();
