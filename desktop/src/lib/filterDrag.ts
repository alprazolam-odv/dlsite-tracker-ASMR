import type { Credit } from "./audio";

export type FilterDragItem = { kind: "tag"; name: string } | { kind: "voice"; credit: Credit };
export type FilterDropTarget = "include" | "exclude";

const TAG_TYPE = "application/x-radar-filter-tag";
const VOICE_TYPE = "application/x-radar-filter-voice";

export function startFilterDrag(event: DragEvent, item: FilterDragItem): void {
  const data = event.dataTransfer;
  if (!data) return;
  if (item.kind === "tag") data.setData(TAG_TYPE, item.name);
  else data.setData(VOICE_TYPE, JSON.stringify(item.credit));
  data.effectAllowed = "copy";
}

export function filterDragKind(data: DataTransfer | null): FilterDragItem["kind"] | null {
  if (data?.types.includes(TAG_TYPE)) return "tag";
  if (data?.types.includes(VOICE_TYPE)) return "voice";
  return null;
}

export function readFilterDrag(data: DataTransfer | null): FilterDragItem | null {
  const kind = filterDragKind(data);
  if (!data || !kind) return null;
  if (kind === "tag") {
    const name = data.getData(TAG_TYPE);
    return name.trim() ? { kind, name } : null;
  }
  try {
    const credit = JSON.parse(data.getData(VOICE_TYPE));
    return typeof credit?.id === "string" && typeof credit.name === "string" && credit.name.trim()
      ? { kind, credit: { id: credit.id, name: credit.name } }
      : null;
  } catch {
    return null;
  }
}
