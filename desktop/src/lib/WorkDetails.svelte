<script lang="ts">
  import type { WorkView } from "./api";
  import type { Credit } from "./audio";
  import CategoryChips from "./CategoryChips.svelte";
  import FormChips from "./FormChips.svelte";
  import GameBadges from "./GameBadges.svelte";
  import type { ContentFlag } from "./tag";
  import { categoriesOf, fmtNum, formsOf, ICONS, workRatingColor, workRatingText } from "./ui";
  import VoiceLine from "./VoiceLine.svelte";

  let {
    game,
    genreNames,
    activeRank = "",
    showBadges = true,
    showRatingCount = true,
    oncats,
    oncatmenu,
    onform,
    onbadge,
    onmaker,
    onvoice,
  }: {
    game: WorkView;
    genreNames: ReadonlyMap<string, string>;
    activeRank?: string;
    showBadges?: boolean;
    showRatingCount?: boolean;
    oncats?: (name: string) => void;
    oncatmenu?: (name: string, event: MouseEvent) => void;
    onform?: (name: string) => void;
    onbadge?: (key: ContentFlag) => void;
    onmaker?: () => void;
    onvoice?: (credit: Credit) => void;
  } = $props();

  const maker = $derived(game.maker || game.maker_id || "未知社团");
  const categories = $derived(categoriesOf(game));
  const forms = $derived(formsOf(game));
  const languages = $derived(game.languages ?? []);
  const minutes = $derived(typeof game.duration_seconds === "number" && game.duration_seconds > 0
    ? Math.round(game.duration_seconds / 60)
    : null);
  const ranks = $derived.by(() => {
    const items = [
      { key: "day", name: "日榜", position: game.rank_day_current },
      { key: "week", name: "周榜", position: game.rank_week_current },
      { key: "month", name: "月榜", position: game.rank_month_current },
      { key: "trend", name: "官方人气", position: game.rank_trend_current },
      ...Object.entries(game.genre_pos ?? {}).sort((a, b) => a[1] - b[1]).map(([id, position]) => ({
        key: `genre:${id}`,
        name: genreNames.get(id) ?? `分类 ${id}`,
        position,
      })),
    ].filter(({ position }) => typeof position === "number" && Number.isFinite(position));
    const index = items.findIndex(({ key }) => key === activeRank);
    if (index > 0) items.unshift(...items.splice(index, 1));
    return items;
  });
</script>

<div class="details">
  <div class="line maker-line">
    {#if onmaker && (game.maker || game.maker_id)}
      <button class="maker" onclick={(event) => { event.stopPropagation(); onmaker?.(); }}
        ondblclick={(event) => event.stopPropagation()}>{maker}</button>
    {:else}
      <span>{maker}</span>
    {/if}
    <span class="id">{game.id}</span>
  </div>
  <VoiceLine {game} {onvoice} wrap />
  {#if categories.length}
    <CategoryChips {categories} ontap={oncats} onmenu={oncatmenu} />
  {/if}
  {#if forms.length || showBadges && (game.voice || game.music || game.video)}
    <div class="line">
      {#if forms.length}<FormChips {forms} ontap={onform} />{/if}
      {#if showBadges}<GameBadges {game} ontap={onbadge} />{/if}
    </div>
  {/if}
  <div class="line">
    <span class="stat"><span aria-hidden="true">{@html ICONS.bag}</span> {fmtNum(game.sales)}</span>
    <span class="stat" style:color={workRatingColor(game)}>
      <span aria-hidden="true">{@html ICONS.star}</span> {workRatingText(game, showRatingCount)}
    </span>
    {#if game.regist_date}
      <span class="stat"><span aria-hidden="true">{@html ICONS.calendar}</span> {game.regist_date.slice(0, 10)}</span>
    {/if}
    {#if minutes !== null || languages.length}
      <span>{minutes === null ? "时长未知" : `${minutes} 分钟`}</span>
      <span>{languages.join(" / ") || "语言未知"}</span>
    {/if}
  </div>
  {#if ranks.length}
    <div class="line ranks">
      <span class="rank-icon" aria-hidden="true">{@html ICONS.rank}</span>
      {#each ranks as rank (rank.key)}
        <span class:active={rank.key === activeRank}>{rank.name} #{rank.position}</span>
      {/each}
    </div>
  {/if}
</div>

<style>
  .details { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
  .line { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
  .maker-line { justify-content: space-between; }
  .id { font-size: 11px; }
  .maker { appearance: none; border: 0; padding: 0; background: none; color: var(--text); font: inherit; text-align: left; cursor: pointer; overflow-wrap: anywhere; }
  .maker:hover, .maker:focus-visible { color: var(--accent); text-decoration: underline; }
  .stat { display: inline-flex; align-items: baseline; gap: 4px; white-space: nowrap; }
  .rank-icon { display: inline-flex; }
  .active { color: var(--accent); font-weight: 650; }
</style>
