import test from "node:test";
import assert from "node:assert/strict";
import { activeFilterCount, applyFilters, emptyFilter, setGenreSelection } from "../src/lib/filter.ts";
import { filterDragKind, readFilterDrag, startFilterDrag } from "../src/lib/filterDrag.ts";

const voice = { id: "1", name: "声优 A" };
const partner = { id: "2", name: "声优 B" };
const work = (id, category, voice_credits, voice_actors) => ({
  id, title: id, category, voice_credits, voice_actors, rating: 4.5, sales: 100, price: 500,
});
const ctx = { viewFilter: { kind: "all" }, favoriteIds: new Set() };

test("included tags and credits all have to match, and any excluded tag removes a work", () => {
  const filter = emptyFilter();
  setGenreSelection(filter, "genres", ["耳语", "助眠"]);
  setGenreSelection(filter, "excludeGenres", ["剧情"]);
  filter.voices = [voice, partner];
  const works = [
    work("official", "耳语 | 助眠", [voice, partner]),
    work("legacy", "耳语 | 助眠", [], "声优 A / 声优 B"),
    work("sameName", "耳语 | 助眠", [{ ...voice, id: "3" }, partner]),
    work("missingCredit", "耳语 | 助眠", [voice]),
    work("missingTag", "耳语", [voice, partner]),
    work("excluded", "耳语 | 助眠 | 剧情", [voice, partner]),
  ];
  assert.deepEqual(applyFilters(works, filter, "sales", ctx).map(({ id }) => id), ["official", "legacy"]);
  assert.equal(activeFilterCount(filter), 5);
});

test("moving a tag between include and exclude preserves the other selections", () => {
  const filter = emptyFilter();
  setGenreSelection(filter, "genres", ["耳语", "助眠"]);
  setGenreSelection(filter, "excludeGenres", ["剧情", "耳语"]);
  assert.deepEqual(filter.genres, ["助眠"]);
  setGenreSelection(filter, "genres", ["助眠", "耳语"]);
  assert.deepEqual(filter.excludeGenres, ["剧情"]);
});

test("drag data preserves exact names and IDs and ignores other drag types", () => {
  const data = new Map();
  const transfer = {
    get types() { return [...data.keys()]; },
    effectAllowed: "none",
    setData: (type, value) => data.set(type, value),
    getData: (type) => data.get(type) ?? "",
  };
  transfer.setData("text/plain", "耳语");
  assert.equal(readFilterDrag(transfer), null);

  for (const item of [{ kind: "tag", name: "耳語 / ささやき" }, { kind: "voice", credit: voice }]) {
    data.clear();
    startFilterDrag({ dataTransfer: transfer }, item);
    assert.equal(transfer.effectAllowed, "copy");
    assert.equal(filterDragKind(transfer), item.kind);
    assert.deepEqual(readFilterDrag(transfer), item);
  }
});
