import { type Credit, type ListenState, hasCredit, sameCredit, recent } from "./audio";
import type { Work } from "./api";

type AudioPreferences = {
  following: Credit[];
  listening: Record<string, ListenState>;
  localIds: string[];
  acknowledged: string[];
};
const KEY = "radar.audio.v1";
function load(): AudioPreferences {
  const defaults: AudioPreferences = { following: [], listening: {}, localIds: [], acknowledged: [] };
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "{}");
    return { ...defaults, ...parsed };
  } catch { return defaults; }
}
class AudioStore {
  data = $state<AudioPreferences>(load());
  persist() { try { localStorage.setItem(KEY, JSON.stringify(this.data)); } catch { /* local storage unavailable */ } }
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
  unread(works: Work[]) {
    const seen = new Set(this.data.acknowledged);
    return works.filter((w) => recent(w) && !seen.has(w.id) && this.data.following.some((c) => hasCredit(w, c)));
  }
  acknowledge(works: Work[]) {
    this.data.acknowledged = [...new Set([...this.data.acknowledged, ...this.unread(works).map((w) => w.id)])].slice(-10000);
    this.persist();
  }
}
export const audioLibrary = new AudioStore();
