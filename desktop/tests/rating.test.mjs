import assert from "node:assert/strict";
import test from "node:test";
import { ratingColor, workRatingColor, workRatingText } from "../src/lib/ui.ts";

test("cards display official scores when present and respect the rating-count preference", () => {
  const game = { rating: 5, rating_precise: 4.83, rating_count: 31 };
  assert.equal(workRatingText(game), "4.83（31）");
  assert.equal(workRatingText(game, false), "4.83");
  assert.equal(workRatingText({ rating_precise: 4.7 }), "4.70");
  assert.equal(workRatingText({ rating: 5, rating_precise: null, rating_count: 31 }), "5（31）");
  assert.equal(workRatingText({ rating: 4.5, rating_precise: null, rating_count: 31 }, false), "4.5");
  assert.equal(workRatingText({ rating: null }), "未评分");
});

test("colour uses the displayed rating and highlights official scores from 4.70", () => {
  assert.equal(ratingColor(4), "#bf5af2");
  assert.equal(ratingColor(4.5), "var(--rating-warm)");
  assert.equal(ratingColor(5), "#ffc700");
  assert.equal(workRatingColor({ rating: 5, rating_precise: 4.5 }), "var(--rating-warm)");
  assert.equal(workRatingColor({ rating: 5, rating_precise: 4.69 }), "#ffc700");
  assert.equal(workRatingColor({ rating: 5, rating_precise: 4.7 }), "#ff375f");
  assert.equal(workRatingColor({ rating: 4.5, rating_precise: null }), "var(--rating-warm)");
  assert.equal(workRatingColor({ rating: null }), "var(--muted)");
});
