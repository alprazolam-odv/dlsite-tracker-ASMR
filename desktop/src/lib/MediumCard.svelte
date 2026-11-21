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

<article class="medium">
  <div class="top">
    <Cover workId={game.id} src={game._cover} width={92} height={122} rounded />
    <div class="info">
      <div class="title">{game.title}</div>
      <WorkDetails {game} {...details} />
    </div>
  </div>
  <div class="bottom">
    <GamePrice {game} {showDiscount} size="sm" />
    <span class="spacer"></span>
    <QuickFollowButton work={game} />
    <HeartButton id={game.id} />
    <button class="open" aria-label="打开作品页" title="打开作品页"
      onclick={(event) => { event.stopPropagation(); onopen(); }}
      ondblclick={(event) => event.stopPropagation()}>
      {@html ICONS.open}
    </button>
  </div>
</article>

<style>
  .medium {
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 11px;
    border-radius: 12px;
    background: var(--panel);
    border: 1px solid var(--border);
    height: 100%;
    box-sizing: border-box;
  }
  .top { display: flex; gap: 11px; align-items: flex-start; }
  .info { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 0; }
  .title { font-size: 13px; font-weight: 600; line-height: 17px; overflow-wrap: anywhere; }
  .bottom { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: auto; }
  .spacer { flex: 1; }
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
