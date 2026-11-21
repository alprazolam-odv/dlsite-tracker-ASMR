<script lang="ts">
  import { flagTag, type TagKind } from "./tag";
  import { startFilterDrag } from "./filterDrag";

  let {
    kind,
    text,
    context = "card",
    removable = false,
    title = "",
    ariaLabel = "",
    pressed,
    dragFilter = false,
    onclick,
    oncontextmenu,
  }: {
    kind: TagKind;
    text: string;
    context?: "card" | "filter";
    removable?: boolean;
    title?: string;
    ariaLabel?: string;
    pressed?: boolean;
    dragFilter?: boolean;
    onclick?: () => void;
    oncontextmenu?: (event: MouseEvent) => void;
  } = $props();

  const icon = $derived(flagTag(kind)?.icon ?? "");
</script>

{#snippet content()}
  {#if pressed !== undefined}<span aria-hidden="true">{pressed ? "✓" : "+"}</span>{/if}
  {#if icon}<span class="icon" aria-hidden="true">{@html icon}</span>{/if}
  {#if text}<span class="text">{text}</span>{/if}
  {#if removable}<span class="remove" aria-hidden="true">×</span>{/if}
{/snippet}

{#if onclick || oncontextmenu}
  <button
    class="chip {kind} {context}"
    title={dragFilter ? [title, "拖到侧栏筛选"].filter(Boolean).join(" · ") : title}
    draggable={dragFilter}
    ondragstart={dragFilter ? (event) => startFilterDrag(event, { kind: "tag", name: text }) : undefined}
    aria-label={ariaLabel || undefined}
    aria-pressed={pressed}
    onclick={onclick}
    oncontextmenu={oncontextmenu}
  >{@render content()}</button>
{:else}
  <span class="chip {kind} {context}" {title}>{@render content()}</span>
{/if}

<style>
  .chip {
    appearance: none;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    border: 0;
    border-radius: 999px;
    padding: 4px 7px;
    font: inherit;
    font-size: 11px;
    line-height: 1;
    white-space: nowrap;
    background: color-mix(in srgb, var(--text) 8%, transparent);
    color: var(--muted);
  }

  button.chip { cursor: pointer; }
  .chip.card { max-width: 100%; white-space: normal; overflow-wrap: anywhere; text-align: left; }
  button.chip[draggable="true"] { cursor: grab; user-select: none; }
  button.chip[aria-pressed] { min-height: 24px; max-width: 100%; white-space: normal; overflow-wrap: anywhere; }
  button.chip[aria-pressed="true"] { color: var(--text); background: color-mix(in srgb, var(--accent) 24%, var(--panel)); }
  button.chip:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  button.chip:hover { filter: brightness(1.12); }
  button.chip.category:hover {
    background: color-mix(in srgb, var(--text) 16%, transparent);
    color: var(--text);
    filter: none;
  }

  .chip.excluded {
    border: 1px dashed var(--muted);
  }

  .chip.form {
    background: var(--form-chip);
    color: #fff;
    font-weight: 600;
    padding-inline: 8px;
  }

  .chip.voice,
  .chip.music,
  .chip.video {
    background: var(--chip-color);
    color: #fff;
    padding: 3px 6px;
  }

  .chip.voice { --chip-color: var(--voice-chip); }
  .chip.music { --chip-color: var(--music-chip); }
  .chip.video { --chip-color: var(--video-chip); }

  .chip.voice .text,
  .chip.music .text,
  .chip.video .text {
    font-size: 10px;
    font-weight: 600;
  }

  .icon { display: inline-flex; flex: none; }

  .chip.filter {
    gap: 7px;
    max-width: 100%;
    padding: 4px 10px;
    font-size: 12px;
  }

  .chip.filter.voice .text,
  .chip.filter.music .text,
  .chip.filter.video .text {
    font-size: 12px;
  }

  .chip.filter.excluded { padding-block: 3px; }
</style>
