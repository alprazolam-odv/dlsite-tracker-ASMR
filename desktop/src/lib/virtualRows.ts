/** Prefix offsets, including the end of the final row. Heights include the row gap. */
export function rowOffsets(count: number, estimate: number, heights: ReadonlyMap<number, number>): Float64Array {
  const offsets = new Float64Array(count + 1);
  offsets.fill(estimate, 1);
  for (const [index, height] of heights) offsets[index + 1] = height;
  for (let index = 1; index <= count; index++) offsets[index] += offsets[index - 1];
  return offsets;
}

export function rowAtOffset(offsets: Float64Array, position: number): number {
  let low = 0;
  let high = offsets.length - 1;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (offsets[mid] <= position) low = mid;
    else high = mid - 1;
  }
  return low;
}
