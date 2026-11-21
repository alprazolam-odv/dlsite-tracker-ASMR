<script lang="ts">
  import type { ComponentProps } from "svelte";
  import { ICONS } from "$lib/ui";
  import Cover from "./Cover.svelte";
  import GamePrice from "./GamePrice.svelte";
  import HeartButton from "./HeartButton.svelte";
  import QuickFollowButton from "./QuickFollowButton.svelte";
  import WorkDetails from "./WorkDetails.svelte";

  let { game, showDiscount = true, onopen, ...details }: ComponentProps<typeof WorkDetails> & {
    showDiscount?: boolean;
    onopen: () => void;
  } = $props();
</script>

<article class="compact">
  <Cover workId={game.id} src={game._cover} width={50} height={64} rounded />
  <div class="main">
    <div class="title">{game.title}</div>
    <WorkDetails {game} {...details} />
  </div>
  <div class="end">
    <GamePrice {game} {showDiscount} size="sm" />
    <div class="actions">
      <QuickFollowButton work={game} />
      <HeartButton id={game.id} />
      <button class="open" aria-label="打开作品页" title="打开作品页"
        onclick={(event) => { event.stopPropagation(); onopen(); }}
        ondblclick={(event) => event.stopPropagation()}>
        {@html ICONS.open}
      </button>
    </div>
  </div>
</article>

<style>
  .compact {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 7px 11px;
    border-radius: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    height: 100%;
    box-sizing: border-box;
  }
  .main { display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 0; }
  .title { font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }
  .end { display: flex; flex-direction: column; align-items: flex-end; flex: none; gap: 6px; }
  .actions { display: flex; align-items: center; gap: 6px; }
  .open {
    appearance: none;
    border: 0;
    background: transparent;
    color: var(--muted);
    padding: 3px;
    border-radius: 5px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    flex: none;
  }
  .open:hover {
    color: var(--text);
    background: color-mix(in srgb, var(--text) 10%, transparent);
  }
</style>
