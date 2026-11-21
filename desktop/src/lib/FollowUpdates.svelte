<script module lang="ts">
  export type FollowTab = "voice" | "circle";
</script>

<script lang="ts">
  import { untrack, type Snippet } from "svelte";
  import type { WorkView } from "$lib/api";
  import { creditKey, type Credit } from "$lib/audio";
  import { makerKeyOf } from "$lib/filter";
  import type { FollowedMaker } from "$lib/library.svelte";
  import Cover from "./Cover.svelte";

  let {
    active = true,
    resetScrollToken = 0,
    tab = $bindable(),
    showTabs,
    voices,
    makers,
    voiceWorkCount,
    voiceUnread,
    circleWorks,
    circleUnreadIds,
    circleUnread,
    lastCheckedAt,
    refreshing = false,
    voiceContent,
    onclose,
    onrefresh,
    onmarkread,
    onopen,
    onmaker,
    onvoice,
    onfindvoices,
    onremovevoice,
    onremovemaker,
  }: {
    active?: boolean;
    resetScrollToken?: number;
    tab: FollowTab;
    showTabs: boolean;
    voices: Credit[];
    makers: FollowedMaker[];
    voiceWorkCount: number;
    voiceUnread: number;
    circleWorks: WorkView[];
    circleUnreadIds: ReadonlySet<string>;
    circleUnread: number;
    lastCheckedAt: number;
    refreshing?: boolean;
    voiceContent: Snippet;
    onclose: () => void;
    onrefresh: () => void;
    onmarkread: () => void;
    onopen: (work: WorkView) => void;
    onmaker: (maker: FollowedMaker) => void;
    onvoice: (credit: Credit) => void;
    onfindvoices: () => void;
    onremovevoice: (credit: Credit) => void;
    onremovemaker: (maker: FollowedMaker) => void;
  } = $props();

  let updatesEl: HTMLDivElement | null = $state(null);
  let savedScrollTop = 0;
  $effect(() => {
    if (active && updatesEl) updatesEl.scrollTop = savedScrollTop;
  });
  $effect(() => {
    void tab;
    void resetScrollToken;
    savedScrollTop = 0;
    untrack(() => updatesEl?.scrollTo({ top: 0 }));
  });

  const unread = $derived(tab === "voice" ? voiceUnread : circleUnread);
  const groups = $derived.by(() => {
    const byMaker = new Map<string, { maker: FollowedMaker; works: WorkView[] }>();
    for (const work of circleWorks) {
      const key = makerKeyOf(work.maker, work.maker_id);
      const group = byMaker.get(key) ?? {
        maker: { key, name: work.maker || "未知社团", maker_id: work.maker_id ?? "" },
        works: [],
      };
      group.works.push(work);
      byMaker.set(key, group);
    }
    return [...byMaker.values()].sort((a, b) =>
      releaseTime(b.works[0].regist_date) - releaseTime(a.works[0].regist_date)
      || a.maker.name.localeCompare(b.maker.name, "zh-Hans-CN"));
  });

  function releaseTime(value: string): number {
    const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
    if (match) return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3])).getTime();
    const stamp = Date.parse(value);
    return Number.isFinite(stamp) ? stamp : 0;
  }

  function ageLabel(value: string): string {
    const stamp = releaseTime(value);
    if (!stamp) return value || "日期未知";
    const days = Math.max(0, Math.floor((Date.now() - stamp) / 86_400_000));
    if (days === 0) return "今天发布";
    if (days === 1) return "昨天发布";
    return `${days} 天前发布`;
  }

  function checkedLabel(): string {
    if (!lastCheckedAt) return "尚未检查";
    return `上次检查 ${new Date(lastCheckedAt).toLocaleString("zh-CN", {
      month: "numeric",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  }
</script>

<div
  class="updates"
  class:inactive={!active}
  bind:this={updatesEl}
  onscroll={(event) => { if (active) savedScrollTop = event.currentTarget.scrollTop; }}
>
  <header>
    <div>
      <h2>{tab === "voice" ? "声优新作" : "社团新作"}</h2>
      <p>查看已入库、近 14 天发售的新作。</p>
    </div>
    <button class="btn" onclick={onclose}>返回作品浏览</button>
  </header>

  <div class="feed-toolbar">
    {#if showTabs}
      <nav aria-label="关注类型">
        <button class="tab" aria-pressed={tab === "voice"} onclick={() => (tab = "voice")}>
          声优新作
          {#if voiceUnread > 0}<span class="badge">{voiceUnread} 部未读</span>{/if}
        </button>
        <button class="tab" aria-pressed={tab === "circle"} onclick={() => (tab = "circle")}>
          社团新作
          {#if circleUnread > 0}<span class="badge">{circleUnread} 部未读</span>{/if}
        </button>
      </nav>
    {:else if unread > 0}
      <span class="badge">{unread} 部未读</span>
    {/if}
    <div class="check">
      <button class="btn" disabled={!unread} onclick={onmarkread}>本页全部标为已读</button>
      <button class="btn primary" disabled={refreshing} onclick={onrefresh}
        title="启动热榜快更，两个关注列表会随作品库刷新">
        {refreshing ? "更新中…" : "检查新作"}
      </button>
    </div>
  </div>

  {#key tab}
    <details class="subscriptions">
      <summary>{tab === "voice" ? `已关注声优 · ${voices.length} 位` : `已关注社团 · ${makers.length} 个`}</summary>
      {#if tab === "voice"}
        {#if voices.length > 0}
          <ul class="subscriptions-list">
            {#each voices as voice (creditKey(voice))}
              <li>
                <button class="name" onclick={() => onvoice(voice)}>{voice.name}</button>
                <button class="btn" aria-label={`取消关注声优 ${voice.name}`} onclick={() => onremovevoice(voice)}>取消关注</button>
              </li>
            {/each}
          </ul>
        {/if}
        <button class="btn find-voices" onclick={onfindvoices}>打开声优目录</button>
      {:else if makers.length > 0}
        <ul class="subscriptions-list">
          {#each makers as maker (maker.key)}
            <li>
              <button class="name" onclick={() => onmaker(maker)}>{maker.name}</button>
              <button class="btn" aria-label={`取消关注社团 ${maker.name}`} onclick={() => onremovemaker(maker)}>取消关注</button>
            </li>
          {/each}
        </ul>
      {:else}
        <p class="find-voices">浏览作品时，点击社团名进入主页，即可关注该社团。</p>
      {/if}
    </details>
  {/key}

  {#if tab === "voice"}
    {#if voiceWorkCount > 0}
      {@render voiceContent()}
    {:else}
      <div class="empty">
        <h3>{voices.length ? "近 14 天没有已入库的声优新作" : "还没有关注声优"}</h3>
        {#if !voices.length}
          <p>可以在声优目录选择想追踪的声优。</p>
          <button class="btn" onclick={onfindvoices}>打开声优目录</button>
        {/if}
      </div>
    {/if}
  {:else if groups.length > 0}
    <div class="feed-meta"><span>{circleWorks.length} 部作品</span><span>{checkedLabel()}</span></div>
    <div class="group-list">
      {#each groups as group (group.maker.key)}
        <section class="maker-group">
          <div class="maker-head">
            <h3><button class="name" onclick={() => onmaker(group.maker)}>{group.maker.name}</button></h3>
            <span>{group.works.length} 部</span>
          </div>
          <div class="work-grid">
            {#each group.works as work (work.id)}
              <button class="work" onclick={() => onopen(work)} title={work.title}>
                <div class="cover-wrap">
                  <Cover workId={work.id} src={work._cover} width="100%" height={168} rounded />
                  {#if circleUnreadIds.has(work.id)}<span class="new">未读</span>{/if}
                </div>
                <span class="title">{work.title}</span>
                <span class="date">{ageLabel(work.regist_date)}</span>
              </button>
            {/each}
          </div>
        </section>
      {/each}
    </div>
  {:else}
    <div class="empty">
      <h3>{makers.length ? "近 14 天没有已入库的社团新作" : "还没有关注社团"}</h3>
      <p>{makers.length ? checkedLabel() : "浏览作品时，点击社团名进入主页，即可关注该社团。"}</p>
    </div>
  {/if}
</div>

<style>
  .updates { min-height: 0; flex: 1; overflow-y: auto; padding: 20px 22px 34px; }
  .updates.inactive { display: none; }
  header, .feed-toolbar, .feed-meta { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  h2, h3, p { margin: 0; }
  h2 { font-size: 22px; }
  p { margin-top: 5px; color: var(--muted); font-size: 13px; }
  .feed-toolbar { margin-top: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
  nav, .check { display: flex; gap: 6px; flex-wrap: wrap; }
  .check { margin-left: auto; }
  .tab { display: inline-flex; align-items: center; gap: 8px; min-height: 36px; padding: 5px 12px; border: 1px solid transparent; border-radius: 8px; background: transparent; color: var(--muted); font: inherit; font-weight: 650; cursor: pointer; }
  .tab:hover, .tab[aria-pressed="true"] { color: var(--text); background: var(--panel); }
  .tab[aria-pressed="true"] { border-color: var(--accent); }
  .badge, .new { border-radius: 999px; padding: 2px 7px; color: var(--text); font-size: 11px; font-weight: 650; }
  .badge { background: color-mix(in srgb, var(--accent) 18%, var(--panel)); }
  .subscriptions { margin: 12px 0 16px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel); }
  summary { width: fit-content; font-weight: 650; cursor: pointer; }
  .subscriptions-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 225px), 1fr)); gap: 6px 16px; margin: 10px 0 0; padding: 0; list-style: none; }
  .subscriptions-list li { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-width: 0; padding-top: 6px; border-top: 1px solid var(--border); }
  .subscriptions-list .btn { flex: none; }
  .find-voices { margin-top: 10px; }
  .feed-meta { margin-bottom: 10px; color: var(--muted); font-size: 12px; }
  .group-list { display: flex; flex-direction: column; gap: 22px; }
  .maker-group { min-width: 0; }
  .maker-head { display: flex; align-items: baseline; gap: 8px; margin-bottom: 9px; color: var(--muted); font-size: 12px; }
  .name { border: 0; background: transparent; color: var(--text); padding: 4px 0; font: inherit; font-size: 14px; font-weight: 700; text-align: left; overflow-wrap: anywhere; cursor: pointer; }
  .name:hover { color: var(--accent); }
  .work-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); gap: 13px; }
  .work { min-width: 0; display: flex; flex-direction: column; gap: 5px; border: 0; background: transparent; color: var(--text); padding: 0; text-align: left; cursor: pointer; }
  .cover-wrap { position: relative; width: 100%; }
  .new { position: absolute; left: 7px; top: 7px; background: var(--panel); box-shadow: 0 1px 5px rgb(0 0 0 / 28%); }
  .title { min-height: 32px; font-size: 12px; line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .date { color: var(--muted); font-size: 12px; }
  .empty { padding: 28px; border: 1px solid var(--border); border-radius: 12px; background: var(--panel); text-align: center; }
  .empty h3 { font-size: 15px; }
  .empty .btn { margin-top: 12px; }
  :is(button, summary):focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
