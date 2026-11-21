<script lang="ts">
  import type { ComponentProps } from "svelte";
  import Cover from "./Cover.svelte";
  import GamePrice from "./GamePrice.svelte";
  import HeartButton from "./HeartButton.svelte";
  import QuickFollowButton from "./QuickFollowButton.svelte";
  import WorkDetails from "./WorkDetails.svelte";

  let { game, showDiscount = true, ...details }: ComponentProps<typeof WorkDetails> & {
    showDiscount?: boolean;
  } = $props();
</script>

<article class="tile">
  <div class="cover-wrap">
    <Cover workId={game.id} src={game._cover} width="100%" height={196} rounded />
    <div class="heart"><HeartButton id={game.id} /></div>
    <div class="follow"><QuickFollowButton work={game} /></div>
  </div>
  <div class="info">
    <div class="title">{game.title}</div>
    <WorkDetails {game} {...details} />
    <GamePrice {game} {showDiscount} size="sm" />
  </div>
</article>

<style>
  .tile {
    display: flex;
    flex-direction: column;
    height: 100%;
    border-radius: 10px;
    background: var(--panel);
    border: 1px solid var(--border);
    box-sizing: border-box;
  }
  .cover-wrap { position: relative; }
  .info { display: flex; flex-direction: column; align-items: stretch; gap: 5px; padding: 8px; }
  .title { font-size: 12px; font-weight: 600; line-height: 16px; overflow-wrap: anywhere; }
  .follow { position: absolute; top: 46px; left: 6px; }
  .heart {
    position: absolute;
    top: 6px;
    right: 6px;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: rgb(0 0 0 / 35%);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .heart :global(.heart) { color: #fff; }
  .heart :global(.heart.on) { color: #ff5d7d; }
</style>
