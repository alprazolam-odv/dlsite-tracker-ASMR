import test from "node:test";
import assert from "node:assert/strict";
import { actorDirectory, dlsiteVoiceSearch, editionGroups, hasCredit, uniqueEditions, bedtimeReason, recentTaggedWorks } from "../src/lib/audio.ts";

const actor = { id: "1", name: "Voice A" };
const actor2 = { id: "2", name: "Voice B" };
const work = (id, extra = {}) => ({ id, title: id, category: "耳语,助眠", voice_credits: [actor], ...extra });

test("DLsite voice search uses the current storefront and encodes creator names as one segment", () => {
  const name = "声優 / A&名前";
  const keyword = encodeURIComponent(`"${name}"`);
  assert.equal(dlsiteVoiceSearch("adult", name), `https://www.dlsite.com/maniax/fsr/=/keyword_creater/${keyword}/work_type/SOU`);
  assert.equal(dlsiteVoiceSearch("all-age", name), `https://www.dlsite.com/home/fsr/=/keyword_creater/${keyword}/work_type/SOU`);
});

test("followed tags match any exact original category and show each recent release once", () => {
  const now = new Date(2026, 10, 21, 12).getTime();
  const release = (id, regist_date, category) => work(id, { regist_date, category });
  const items = [
    release("within", "2026-11-08", "剧情、旧友"),
    release("multiple", "2026-11-21", " 剧情 | 旧友 | 剧情 "),
    release("partial", "2026-11-20", "老友与旧友"),
    release("expired", "2026-11-07", "剧情"),
    release("future", "2026-11-22", "旧友"),
    release("absent", "2026-11-21", ""),
  ];
  assert.deepEqual(recentTaggedWorks(items, ["旧友", "剧情"], now).map(w => w.id), ["multiple", "within"]);
  assert.deepEqual(recentTaggedWorks(items, [], now), []);
});

test("actor directory and intersecting official credits", () => {
  const entries = [work("RJ100000"), work("RJ100001", { voice_credits: [actor, actor2] }), work("RJ100002", { voice_actors: "Voice A", voice_credits: [] })];
  assert.deepEqual(actorDirectory(entries).map((x) => [x.credit.name, x.count]), [["Voice A", 3], ["Voice B", 1]]);
  assert.equal(entries.filter((w) => [actor, actor2].every((credit) => hasCredit(w, credit))).length, 1);
});

test("versions grouped only by explicit identifiers and filtered translation retained", () => {
  const source = work("RJ100000", { related_ids: ["RJ100001"] });
  const translated = work("RJ100001", { original_id: source.id });
  const unrelated = work("RJ100002", { title: source.title });
  const groups = editionGroups([translated, source, unrelated]);
  assert.deepEqual(uniqueEditions([translated, source, unrelated], groups).map((x) => x.id), [source.id, unrelated.id]);
  assert.deepEqual(uniqueEditions([translated, unrelated], groups).map((x) => x.id), [translated.id, unrelated.id]);
  assert.deepEqual(uniqueEditions([translated, source], groups, false).map((x) => x.id), [translated.id]);
});

test("bedtime recommendation requires a known fitting duration and respects disliked tags", () => {
  const known = work("RJ100000", { duration_seconds: 1800, rating: 4.5 });
  assert.ok(bedtimeReason(known, 30, {}, [actor]).reason.includes("Voice A"));
  assert.equal(bedtimeReason(known, 20, {}, []), null);
  assert.equal(bedtimeReason(known, 30, { 助眠: "less" }, []), null);
  assert.equal(bedtimeReason(work("RJ100001"), 60, {}, []), null);
  const candidate = bedtimeReason(work("RJ100001"), 60, {}, [], true);
  assert.ok(candidate.reason.includes("时长未知"));
  assert.ok(candidate.score < bedtimeReason(known, 60, {}, []).score);
});
