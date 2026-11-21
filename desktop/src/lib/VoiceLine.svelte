<script lang="ts">
  import type { WorkView } from "./api";
  import { creditsOf, creditKey, type Credit } from "./audio";
  let { game, onvoice }: { game: WorkView; onvoice?: (credit: Credit) => void } = $props();
  const credits = $derived(creditsOf(game));
</script>
{#if credits.length}
  <div class="voice-line" title={credits.map((c) => c.name).join(" / ")}>
    <span>声优：</span>
    {#each credits as credit (creditKey(credit))}
      {#if onvoice}
        <button title={`查看声优「${credit.name}」的作品`} onclick={(event) => { event.stopPropagation(); onvoice?.(credit); }}
          ondblclick={(event) => event.stopPropagation()}>{credit.name}</button>
      {:else}<span>{credit.name}</span>{/if}
    {/each}
  </div>
{/if}
<style>
  .voice-line { display: flex; align-items: center; gap: 5px; color: var(--muted); min-width: 0; overflow: auto; scrollbar-width: none; white-space: nowrap; font-size: 12px; line-height: 18px; }
  button { appearance: none; border: 0; padding: 0; background: transparent; color: var(--text); font: inherit; cursor: pointer; white-space: nowrap; }
  button:hover, button:focus-visible { color: var(--accent); text-decoration: underline; }
</style>
