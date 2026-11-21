import test from "node:test";
import assert from "node:assert/strict";
import { get } from "svelte/store";
import { createExternalLibrary, visibleLibraryWorks } from "../src/lib/externalLibrary.ts";

const endpoint = "http://library.test/lookup";
const catalog = ["RJ000001", "RJ000002", "RJ000003", "RJ000004"].map(id => ({ id }));
const initial = {
  complete: true, collected: ["RJ1", "RJ2"], excluded: ["RJ2", "RJ3"],
  absent: ["RJ3", "RJ4"], unknown: [],
};
function memoryStorage() {
  const items = new Map();
  return { getItem: k => items.get(k), setItem: (k, v) => items.set(k, v), removeItem: k => items.delete(k) };
}

test("optional startup, profile cache, manual refresh and independent filters", async () => {
  const storage = memoryStorage();
  let calls = 0;
  const store = createExternalLibrary(async () => { calls++; return initial; }, () => storage);
  store.useProfile("adult");
  await store.setWorks(catalog);
  assert.equal(calls, 0);
  await store.configure(endpoint);
  await store.setWorks([...catalog].reverse());
  assert.equal(calls, 1);
  await store.refresh();
  assert.equal(calls, 2);
  const visible = () => visibleLibraryWorks(catalog, get(store)).map(w => w.id);
  store.setFilter("hideCollected", true);
  assert.deepEqual(visible(), ["RJ000003", "RJ000004"]);
  store.setFilter("hideExcluded", true);
  assert.deepEqual(visible(), ["RJ000004"]);
  store.setFilter("hideCollected", false);
  assert.deepEqual(visible(), ["RJ000001", "RJ000004"]);

  const offline = createExternalLibrary(async () => { throw new Error("offline"); }, () => storage);
  offline.useProfile("all-age");
  assert.equal(get(offline).endpoint, "");
  offline.useProfile("adult");
  assert.equal(get(offline).hideExcluded, true);
  assert.deepEqual(get(offline).marks.collected, new Set(["1", "2"]));
  await offline.setWorks(catalog);
  assert.match(get(offline).error, /offline/);
  assert.equal(get(offline).syncedAt, get(store).syncedAt);
  assert.deepEqual(get(offline).marks, get(store).marks);
  await offline.configure("");
  assert.equal(visibleLibraryWorks(catalog, get(offline)), catalog);
  offline.useProfile("adult");
  assert.equal(get(offline).endpoint, "");
});

test("unknown retains prior ownership, exclusions update independently, resolved absence clears old marks", async () => {
  let response = initial;
  const store = createExternalLibrary(async () => response, () => storage);
  const storage = memoryStorage();
  store.useProfile("adult");
  await store.setWorks(catalog);
  await store.configure(endpoint);
  response = { complete: false, unknown: ["RJ1", "RJ3"], absent: ["RJ2"], collected: ["RJ4"], excluded: ["RJ1"] };
  await store.refresh();
  const { marks, partial } = get(store);
  assert.equal(partial, true);
  assert.deepEqual(marks.collected, new Set(["1", "4"]));
  assert.deepEqual(marks.excluded, new Set(["1"]));
  assert.deepEqual(marks.unknown, new Set(["1", "3"]));
  for (const bad of [
    { found_count: 2, missing: ["RJ1"], complete: true },
    { ...response, complete: true },
    { ...response, absent: [] },
    { ...response, absent: ["RJ1", "RJ2"] },
    { ...response, excluded: ["RJ5"] },
  ]) {
    response = bad;
    await store.refresh();
    assert.ok(get(store).error);
    assert.equal(get(store).marks, marks);
  }
});

test("deduplicates and batches at 5000, reuses scan token, publishes only after all batches succeed", async () => {
  const works = Array.from({ length: 5001 }, (_, i) => ({ id: "RJ" + (i + 1) }));
  const storage = memoryStorage();
  const calls = [];
  let fail = false;
  const store = createExternalLibrary(async (_url, ids, _signal, snapshot) => {
    calls.push([ids.length, snapshot]);
    if (fail && snapshot) throw new Error("offline");
    return { complete: true, collected: fail ? [] : ids, absent: fail ? ids : [], excluded: [], unknown: [], snapshot: "scan" };
  }, () => storage);
  store.useProfile("adult");
  await store.setWorks([...works, { id: "RJ00001" }, { id: "other" }]);
  await store.configure(endpoint);
  assert.deepEqual(calls, [[5000, undefined], [1, "scan"]]);
  assert.equal(get(store).marks.collected.size, 5001);
  fail = true;
  const cached = storage.getItem("radar.externalLibrary.v1.adult");
  await store.refresh();
  assert.match(get(store).error, /offline/);
  assert.equal(get(store).marks.collected.size, 5001);
  assert.equal(storage.getItem("radar.externalLibrary.v1.adult"), cached);
});

test("late responses cannot restore marks after changing or disabling an endpoint", async () => {
  let finish;
  const storage = memoryStorage();
  const store = createExternalLibrary(async (url) => {
    if (url === endpoint) return new Promise(r => { finish = r; });
    throw new Error("unavailable");
  }, () => storage);
  store.useProfile("adult");
  await store.setWorks(catalog);
  const first = store.configure(endpoint);
  await store.configure("https://other.test/lookup");
  finish(initial);
  await first;
  assert.equal(get(store).marks.collected.size, 0);
  assert.match(get(store).error, /unavailable/);
  const second = store.configure(endpoint);
  await store.configure("");
  finish(initial);
  await second;
  assert.equal(get(store).endpoint, "");
  assert.equal(get(store).marks.collected.size, 0);
});

test("online creator pages check new RJ IDs without changing Radar's saved marks", async () => {
  const storage = memoryStorage();
  const calls = [];
  const store = createExternalLibrary(async (_url, ids) => {
    calls.push(ids);
    if (ids.length === catalog.length) return initial;
    return { complete: false, collected: ["RJ5"], absent: ["RJ6"], excluded: ["RJ5"], unknown: ["RJ1"] };
  }, () => storage);
  store.useProfile("adult");
  await store.setWorks(catalog);
  await store.configure(endpoint);
  const onlyOnline = [{ id: "RJ000005" }, { id: "RJ000006" }, catalog[0]];
  const cached = storage.getItem("radar.externalLibrary.v1.adult");
  const marks = await store.lookupPage(onlyOnline, new AbortController());
  assert.deepEqual(calls[1], ["RJ000005", "RJ000006", "RJ000001"]);
  assert.deepEqual(marks.collected, new Set(["5", "1"]));
  assert.deepEqual(marks.excluded, new Set(["5"]));
  for (const flag of ["hideCollected", "hideExcluded"]) {
    const visible = visibleLibraryWorks(onlyOnline, { ...get(store), marks, [flag]: true });
    assert.ok(!visible.some(work => work.id === "RJ000005"));
  }
  assert.deepEqual(get(store).marks.collected, new Set(["1", "2"]));
  assert.equal(storage.getItem("radar.externalLibrary.v1.adult"), cached);
});

test("an unlisted language edition marks its whole group and uses the same collected filter", async () => {
  const simplerChinese = "RJ000003";
  const works = [
    { id: "RJ000001", related_ids: [simplerChinese] },
    { id: "RJ000002", original_id: "RJ000001" },
    { id: "RJ000004", title: "同名但无官方关联" },
  ];
  const storage = memoryStorage();
  let collected = [simplerChinese];
  let unknown = [];
  const store = createExternalLibrary(async (_url, ids) => {
    assert.ok(ids.includes(simplerChinese));
    return {
      complete: !unknown.length, collected, unknown, excluded: [simplerChinese],
      absent: ids.filter(id => !collected.includes(id) && !unknown.includes(id)),
    };
  }, () => storage);
  store.useProfile("adult");
  await store.setWorks(works);
  await store.configure(endpoint);
  assert.deepEqual(get(store).marks.otherEdition, new Set(["1", "2"]));
  assert.deepEqual(get(store).marks.excluded, new Set(["3"]));
  assert.deepEqual(visibleLibraryWorks(works, get(store)), works);
  store.setFilter("hideCollected", true);
  assert.deepEqual(visibleLibraryWorks(works, get(store)), [works[2]]);

  const offline = createExternalLibrary(async () => { throw new Error("offline"); }, () => storage);
  offline.useProfile("adult");
  await offline.setWorks(works);
  assert.deepEqual(get(offline).marks.otherEdition, new Set(["1", "2"]));

  collected = [];
  unknown = [works[0].id, simplerChinese];
  await store.refresh();
  assert.deepEqual(get(store).marks.otherEdition, new Set(["1", "2"]));
  assert.deepEqual(get(store).marks.unknown, new Set(["1", "2", "3"]));
  unknown = [works[0].id];
  await store.refresh();
  assert.equal(get(store).marks.collected.size, 0);
  assert.deepEqual(visibleLibraryWorks(works, get(store)), works);
});

test("online editions use official links from the page and radar without copying exclusions", async () => {
  const storage = memoryStorage();
  const calls = [];
  const store = createExternalLibrary(async (_url, ids) => {
    calls.push(ids);
    return {
      complete: true, collected: ["RJ000003"], absent: ids.filter(id => id !== "RJ000003"),
      excluded: ["RJ000003"], unknown: [],
    };
  }, () => storage);
  store.useProfile("adult");
  await store.setWorks([{ id: "RJ000003", original_id: "RJ000001" }]);
  await store.configure(endpoint);
  const page = [{ id: "RJ000005", original_id: "RJ00000001" }, { id: "RJ000006" }];
  const marks = await store.lookupPage(page, new AbortController());
  assert.deepEqual(new Set(calls[1]), new Set(["RJ000005", "RJ000006", "RJ000001", "RJ000003"]));
  assert.ok(marks.otherEdition.has("5"));
  assert.ok(!marks.excluded.has("5"));
  assert.deepEqual(visibleLibraryWorks(page, { ...get(store), marks, hideCollected: true }), [page[1]]);
  assert.ok(!get(store).marks.collected.has("5"));
});
