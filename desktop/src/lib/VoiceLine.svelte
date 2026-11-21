<script lang="ts">
  import type { WorkView } from "./api";
  import { creditsOf, creditKey, type Credit } from "./audio";
  import { startFilterDrag } from "./filterDrag";
  let { game, onvoice, wrap = false }: { game: WorkView; onvoice?: (credit: Credit) => void; wrap?: boolean } = $props();
  const credits = $derived(creditsOf(game));
</script>
{#if credits.length}
  <div class="voice-line" class:wrap title={wrap ? undefined : credits.map((c) => c.name).join(" / ")}>
    <span>声优：</span>
    {#each credits as credit (creditKey(credit))}
      {#if onvoice}
        <button title={`点击查看声优「${credit.name}」的作品 · 拖到侧栏筛选`} draggable="true"
          ondragstart={(event) => startFilterDrag(event, { kind: "voice", credit })}
          onclick={(event) => { event.stopPropagation(); onvoice?.(credit); }}
          ondblclick={(event) => event.stopPropagation()}>{credit.name}</button>
      {:else}<span>{credit.name}</span>{/if}
    {/each}
  </div>
{/if}
<style>
  .voice-line { display: flex; align-items: center; gap: 5px; color: var(--muted); min-width: 0; overflow: auto; scrollbar-width: none; white-space: nowrap; font-size: 12px; line-height: 18px; }
  .voice-line.wrap { flex-wrap: wrap; column-gap: 7px; row-gap: 1px; white-space: normal; overflow: visible; overflow-wrap: anywhere; }
  button { appearance: none; border: 0; padding: 0; background: transparent; color: var(--text); font: inherit; cursor: grab; user-select: none; white-space: nowrap; }
  .wrap button { text-align: left; white-space: normal; }
  button:hover, button:focus-visible { color: var(--accent); text-decoration: underline; }
</style>
