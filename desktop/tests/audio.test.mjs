import test from "node:test";
import assert from "node:assert/strict";
import { actorDirectory, editionGroups, hasCredit, uniqueEditions, bedtimeReason } from "../src/lib/audio.ts";

const actor = { id: "1", name: "Voice A" };
const actor2 = { id: "2", name: "Voice B" };
const work = (id, extra = {}) => ({ id, title: id, category: "耳语,助眠", voice_credits: [actor], ...extra });

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
});

test("bedtime recommendation requires a known fitting duration and respects disliked tags", () => {
  const known = work("RJ100000", { duration_seconds: 1800, rating: 4.5 });
  assert.ok(bedtimeReason(known, 30, {}, [actor]).reason.includes("Voice A"));
  assert.equal(bedtimeReason(known, 20, {}, []), null);
  assert.equal(bedtimeReason(known, 30, { 助眠: "less" }, []), null);
  assert.equal(bedtimeReason(work("RJ100001"), 60, {}, []), null);
});
