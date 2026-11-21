import assert from "node:assert/strict";
import test from "node:test";
import { rowAtOffset, rowOffsets } from "../src/lib/virtualRows.ts";

test("measured row heights affect all following offsets while other rows use the estimate", () => {
  const offsets = rowOffsets(4, 100, new Map([[1, 230], [3, 80]]));
  assert.deepEqual([...offsets], [0, 100, 330, 430, 510]);
  assert.equal(rowAtOffset(offsets, 99), 0);
  assert.equal(rowAtOffset(offsets, 100), 1);
  assert.equal(rowAtOffset(offsets, 329), 1);
  assert.equal(rowAtOffset(offsets, 330), 2);
  assert.equal(rowAtOffset(offsets, 509), 3);
  assert.equal(rowAtOffset(offsets, 510), 4);
  assert.equal(rowAtOffset(rowOffsets(0, 100, new Map()), 0), 0);
});
