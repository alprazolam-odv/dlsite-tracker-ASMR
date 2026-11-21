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

<article class="large">
  <Cover workId={game.id} src={game._cover} width={110} height={146} rounded />
  <div class="main">
    <div class="headline">
      <div class="title">{game.title}</div>
      <GamePrice {game} {showDiscount} />
    </div>
    <WorkDetails {game} {...details} />
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
  .large {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 13px;
    border-radius: 14px;
    background: var(--panel);
    border: 1px solid var(--border);
    height: 100%;
    box-sizing: border-box;
  }
  .main {
    display: flex;
    flex-direction: column;
    gap: 5px;
    flex: 1;
    min-width: 0;
    min-height: 146px;
  }
  .headline { display: flex; align-items: baseline; gap: 12px; }
  .title { flex: 1; min-width: 0; font-size: 14px; font-weight: 600; line-height: 18px; overflow-wrap: anywhere; }
  .actions { display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: auto; }
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
