<script lang="ts">
  import { invoke } from "@tauri-apps/api/core";
  import { untrack } from "svelte";
  import type { WorkView, Profile } from "./api";
  import {
    AUDIO_THEMES, LISTEN_LABELS, actorDirectory, bedtimeReason, creditKey,
    creditsOf, dlsiteVoiceSearch, durationLabel, editionGroups, hasCredit, sameCredit, themesOf,
    uniqueEditions, type Credit, type ListenState,
  } from "./audio";
  import { audioLibrary } from "./audio.svelte";
  import { prefs } from "./prefs.svelte";
  import Cover from "./Cover.svelte";
  import FollowTags from "./FollowTags.svelte";
  import QuickFollowButton from "./QuickFollowButton.svelte";
  import { categoriesOf } from "./ui";
  import { startFilterDrag } from "./filterDrag";

  let {
    works, ageProfile = "adult", initialActor = null, followedWorks, unreadIds,
    onactor, onmaker, onopen, onclose, closeLabel = "返回作品浏览", onreload,
  }: {
    works: WorkView[];
    ageProfile?: Profile;
    initialActor?: Credit | null;
    followedWorks?: WorkView[];
    unreadIds: ReadonlySet<string>;
    onactor?: (credit: Credit) => void;
    onmaker?: (work: WorkView) => void;
    onopen: (url: string) => void;
    onclose?: () => void;
    closeLabel?: string;
    onreload: () => Promise<void>;
  } = $props();
  let tab = $state<"browse" | "bedtime">("browse");
  let selected = $state<Credit[]>(untrack(() => initialActor ? [initialActor] : []));
  let actorQuery = $state("");
  let query = $state("");
  let theme = $state<string[]>([]);
  let language = $state("");
  let listening = $state("");
  let localOnly = $state(false);
  let previewOnly = $state(false);
  let duration = $state("");
  let bedtimeMinutes = $state(90);
  let bedtimeUnknown = $state(true);
  let collapseVersions = $state(untrack(() => !initialActor));
  let maxRows = $state(40);
  let actorLimit = $state(12);
  let scanning = $state(false);
  let detailsBusy = $state(false);
  let message = $state("");
  let workspaceEl: HTMLDivElement | null = $state(null);

  const directory = $derived(actorDirectory(works));
  const actorResults = $derived(directory.filter(({ credit }) =>
    credit.name.toLowerCase().includes(actorQuery.trim().toLowerCase())));
  const allLanguages = $derived([...new Set(works.flatMap((w) => w.languages ?? []))].sort());
  const groups = $derived(editionGroups(works));
  const byId = $derived(new Map(works.map((work) => [work.id, work])));
  const localIds = $derived(new Set(audioLibrary.data.localIds));
  const embedded = $derived(followedWorks !== undefined);
  const profile = $derived(selected.length === 1 ? selected[0] : null);
  const profileWorks = $derived(profile ? works.filter((w) => hasCredit(w, profile!)) : []);
  const circleResults = $derived.by(() => {
    const counts = new Map<string, { name: string; count: number }>();
    for (const work of profileWorks) {
      const name = work.maker || "";
      if (!name) continue;
      const k = work.maker_id || name;
      counts.set(k, { name, count: (counts.get(k)?.count ?? 0) + 1 });
    }
    return [...counts.values()].sort((a, b) => b.count - a.count).slice(0, 10);
  });
  const collaborators = $derived(actorDirectory(profileWorks).filter(({ credit }) =>
    profile && !sameCredit(credit, profile)).slice(0, 8));
  const similar = $derived.by(() => {
    if (!profileWorks.length || !profile) return [];
    const tags = new Set(profileWorks.flatMap(themesOf));
    if (!tags.size) return [];
    const candidates = new Map<string, { credit: Credit; shared: Set<string> }>();
    for (const work of works) {
      const overlap = themesOf(work).filter((tag) => tags.has(tag));
      if (!overlap.length) continue;
      for (const credit of creditsOf(work)) {
        if (sameCredit(credit, profile) || collaborators.some((item) => sameCredit(item.credit, credit))) continue;
        const key = creditKey(credit);
        const item = candidates.get(key) ?? { credit, shared: new Set<string>() };
        overlap.forEach((tag) => item.shared.add(tag));
        candidates.set(key, item);
      }
    }
    return [...candidates.values()].sort((a, b) => b.shared.size - a.shared.size).slice(0, 8);
  });

  const results = $derived.by(() => {
    const keyword = query.trim().toLowerCase();
    let found = (followedWorks ?? works).filter((w) => {
      if (selected.length && !selected.every((credit) => hasCredit(w, credit))) return false;
      if (keyword && ![w.title, w.id, w.maker, w.voice_actors ?? "", ...creditsOf(w).map((c) => c.name)]
        .join(" ").toLowerCase().includes(keyword)) return false;
      if (theme.length && !theme.every((tag) => themesOf(w).includes(tag))) return false;
      if (language && (language === "unknown" ? !!w.languages?.length : !(w.languages ?? []).includes(language))) return false;
      if (listening && (audioLibrary.data.listening[w.id] ?? "unmarked") !== listening) return false;
      if (localOnly && !localIds.has(w.id)) return false;
      if (previewOnly && !w.has_preview) return false;
      const seconds = w.duration_seconds ?? 0;
      if (duration === "unknown" && seconds > 0) return false;
      if (duration === "short" && (seconds <= 0 || seconds > 30 * 60)) return false;
      if (duration === "medium" && (seconds <= 30 * 60 || seconds > 90 * 60)) return false;
      if (duration === "long" && seconds <= 90 * 60) return false;
      if (tab === "bedtime" && (["heard", "disliked"].includes(audioLibrary.data.listening[w.id] ?? "")
        || !bedtimeReason(w, bedtimeMinutes, prefs.data.tasteProfile, audioLibrary.data.following, bedtimeUnknown))) return false;
      return true;
    });
    if (tab === "bedtime") found.sort((a, b) =>
      (bedtimeReason(b, bedtimeMinutes, prefs.data.tasteProfile, audioLibrary.data.following, bedtimeUnknown)?.score ?? 0) -
      (bedtimeReason(a, bedtimeMinutes, prefs.data.tasteProfile, audioLibrary.data.following, bedtimeUnknown)?.score ?? 0));
    else found.sort((a, b) => (b.regist_date ?? "").localeCompare(a.regist_date ?? "") || b.id.localeCompare(a.id));
    return collapseVersions ? uniqueEditions(found, groups, tab !== "bedtime") : found;
  });

  function switchTab(next: typeof tab) {
    tab = next; maxRows = 40; selected = [];
    query = ""; theme = []; language = ""; duration = ""; listening = ""; previewOnly = false; localOnly = false;
    workspaceEl?.scrollTo({ top: 0 });
  }
  function openActor(credit: Credit) {
    if (onactor) {
      onactor(credit);
      return;
    }
    switchTab("browse");
    selected = [credit];
    collapseVersions = false;
  }
  function toggleActor(credit: Credit) {
    selected = selected.some((c) => sameCredit(c, credit))
      ? selected.filter((c) => !sameCredit(c, credit)) : [...selected, credit];
    tab = "browse"; maxRows = 40;
  }
  async function scan() {
    scanning = true; message = "";
    try {
      const ids = await invoke<string[] | null>("scan_local_audio");
      if (ids !== null) {
        audioLibrary.setLocalIds(ids);
        message = `已识别 ${ids.length} 个 RJ 编号，其中 ${works.filter((w) => ids.includes(w.id)).length} 部在当前作品库。`;
      }
    } catch (error) { message = String(error); }
    finally { scanning = false; }
  }
  async function fillDetails(id: string | null = null) {
    detailsBusy = true;
    message = id ? "正在补齐选中作品的公开资料…" : "正在按站点限速补齐最多 10 部作品，可能需要几分钟…";
    try { message = await invoke<string>("refresh_audio_details", { workno: id }); }
    catch (error) { message = String(error); }
    finally {
      try { await onreload(); } catch { /* 原有作品数据保留 */ }
      detailsBusy = false;
    }
  }
  function officialWork(id: string) {
    if (!/^RJ\d{6}(?:\d{2})?$/.test(id)) return;
    if (ageProfile === "all-age" && !byId.has(id)) return;
    onopen(byId.get(id)?.url ?? `https://www.dlsite.com/maniax/work/=/product_id/${id}.html`);
  }
</script>

<div class="audio-workspace" class:embedded bind:this={workspaceEl}>
  {#if !embedded}
  <header class="workspace-title">
    <div>
      <h2>{profile ? `${profile.name} · 声优作品` : "声优目录"}</h2>
    </div>
    <button onclick={onclose}>{closeLabel}</button>
  </header>
  <nav class="toolbar" aria-label="声优目录与推荐">
    <button aria-pressed={tab === "browse"} class:active={tab === "browse"} onclick={() => switchTab("browse")}>音声与声优</button>
    <button aria-pressed={tab === "bedtime"} class:active={tab === "bedtime"} onclick={() => switchTab("bedtime")}>睡前推荐</button>
    <span class="grow"></span>
    <button disabled={scanning} onclick={scan}>{scanning ? "识别中…" : "识别本地音频"}</button>
    <button disabled={detailsBusy} onclick={() => void fillDetails()}>{detailsBusy ? "补齐中…" : "补齐音声资料（10 部）"}</button>
  </nav>
  <details class="actors" open={tab === "browse" && !profile}>
    <summary>声优目录 · {directory.length} 位</summary>
    <div class="actor-search">
      <label>搜索声优 <input placeholder="姓名" bind:value={actorQuery} oninput={() => (actorLimit = 12)} /></label>
      <button onclick={() => (selected = [])} disabled={!selected.length}>清除声优筛选</button>
      <span class="hint">点击姓名查看作品；「加入」可筛选多位声优的合作作品。</span>
    </div>
    <div class="actor-grid">
      {#each actorResults.slice(0, actorLimit) as { credit, count } (creditKey(credit))}
        <div class="actor">
          <button class="actor-name" onclick={() => openActor(credit)} title={credit.name}>{credit.name} · {count} 部</button>
          <button class:active={selected.some((c) => sameCredit(c, credit))}
            aria-pressed={selected.some((c) => sameCredit(c, credit))}
            onclick={() => toggleActor(credit)}>{selected.some((c) => sameCredit(c, credit)) ? "移除" : "加入"}</button>
          <button aria-pressed={audioLibrary.isFollowing(credit)} class:active={audioLibrary.isFollowing(credit)}
            onclick={() => audioLibrary.toggle(credit)}>{audioLibrary.isFollowing(credit) ? "已关注" : "关注"}</button>
        </div>
      {/each}
    </div>
    {#if actorResults.length > actorLimit}<button class="more" onclick={() => (actorLimit += 24)}>更多声优</button>{/if}
    {#if !actorResults.length}<p class="hint">没有匹配声优；旧库可先补齐资料。</p>{/if}
  </details>

  {/if}
  {#if message}<p class="notice" role="status">{message}</p>{/if}

  {#if profile}
    <section class="panel">
      <div class="toolbar">
        <h3>雷达目录 · {profileWorks.length} 部</h3>
        <button onclick={() => onopen(dlsiteVoiceSearch(ageProfile, profile!.name))}>在 DLsite 搜索声优作品</button>
        <button class:active={audioLibrary.isFollowing(profile)} onclick={() => audioLibrary.toggle(profile!)}>{audioLibrary.isFollowing(profile) ? "取消关注" : "关注声优"}</button>
        <button onclick={() => (selected = [])}>全部音声</button>
      </div>
      <div class="insights">
        <div><h4>合作社团</h4><div class="chips">
          {#each circleResults as circle (circle.name)}
            <button onclick={() => { query = circle.name; }}>{circle.name} · {circle.count}</button>
          {/each}
          {#if !circleResults.length}<span class="hint">暂无记录</span>{/if}
        </div></div>
        <div><h4>合作声优</h4><div class="chips">
          {#each collaborators as { credit, count } (creditKey(credit))}
            <button onclick={() => toggleActor(credit)}>{credit.name} · {count}</button>
          {/each}
          {#if !collaborators.length}<span class="hint">暂无记录</span>{/if}
        </div></div>
        <div><h4>标签相近的声优</h4><div class="chips">
          {#each similar as { credit, shared } (creditKey(credit))}
            <button title={[...shared].join("、")} onclick={() => openActor(credit)}>{credit.name} · {shared.size} 类相近</button>
          {/each}
          {#if !similar.length}<span class="hint">暂无记录</span>{/if}
        </div></div>
      </div>
    </section>
  {/if}

  {#if tab === "bedtime"}
    <section class="panel">
      <h3>今晚想听多久？</h3>
      <label>最多 <input type="number" min="5" max="480" step="5" bind:value={bedtimeMinutes} /> 分钟</label>
      <label><input type="checkbox" bind:checked={bedtimeUnknown} /> 同时显示时长未知的备选</label>
      <p class="hint">优先推荐明确标注助眠、耳语、采耳等标签且符合时长要求的作品；结合你的口味和关注，排除已听和不喜欢的作品。未知时长的备选排在后面，无法保证符合设定时间。</p>
    </section>
  {/if}
  <section class="filters panel" aria-label="音声筛选">
    <div class="toolbar">
      <label>搜索作品 <input placeholder="作品名、RJ、社团、声优" bind:value={query} /></label>
      <label>语言/版本
        <select bind:value={language}><option value="">全部</option><option value="unknown">未知</option>
          {#each allLanguages as lang}<option value={lang}>{lang}</option>{/each}
        </select>
      </label>
      <label>播放时长
        <select bind:value={duration}><option value="">全部</option><option value="short">30 分钟以内</option><option value="medium">30–90 分钟</option><option value="long">90 分钟以上</option><option value="unknown">未知</option></select>
      </label>
      <label>收听状态
        <select bind:value={listening}><option value="">全部</option><option value="unmarked">未标记</option>
          {#each Object.entries(LISTEN_LABELS) as [key, label]}<option value={key}>{label}</option>{/each}
        </select>
      </label>
    </div>
    <div class="chips">
      {#each AUDIO_THEMES as group}
        <button aria-pressed={theme.includes(group.name)} class:active={theme.includes(group.name)}
          onclick={() => (theme = theme.includes(group.name) ? theme.filter((t) => t !== group.name) : [...theme, group.name])}>{group.name}</button>
      {/each}
    </div>
    {#if selected.length}
      <div class="chips"><span>同时包含声优：</span>{#each selected as credit (creditKey(credit))}
        <button onclick={() => toggleActor(credit)}>{credit.name} ×</button>
      {/each}</div>
    {/if}
    <div class="toolbar checkboxes">
      <label><input type="checkbox" bind:checked={localOnly} /> 仅本地已有</label>
      <label><input type="checkbox" bind:checked={previewOnly} /> 有官方试听信息</label>
      <label><input type="checkbox" bind:checked={collapseVersions} /> 合并原作与译版</label>
      {#if audioLibrary.data.localIds.length}
        <button onclick={() => { audioLibrary.setLocalIds([]); message = "已清除本地识别记录，原始文件未改动。"; }}>清除本地识别记录</button>
      {/if}
    </div>
  </section>
  <div class="results-label"><strong>{results.length} 部作品</strong><span class="hint">基于当前本机库 · 已识别本地 {localIds.size} 个 RJ</span></div>
  <div class="results">
    {#each results.slice(0, maxRows) as work (work.id)}
      <article class="audio-row">
        <Cover workId={work.id} src={work._cover} width={72} height={94} rounded />
        <div class="work-info">
          <button class="work-title" title={work.title} onclick={() => officialWork(work.id)}>{work.title}</button>
          <div class="sub">{work.id} ·
            {#if onmaker && (work.maker || work.maker_id)}
              <button class="maker-link" title="查看社团的 DLsite 音声作品"
                onclick={() => onmaker?.(work)}>{work.maker || work.maker_id}</button>
            {:else}{work.maker || "社团未知"}{/if}
            · {work.regist_date?.slice(0, 10) || "日期未知"}
            {#if localIds.has(work.id)}<strong> · 本地已有</strong>{/if}
            {#if unreadIds.has(work.id)}<strong> · 未读新作</strong>{/if}
          </div>
          <div class="chips">
            {#each creditsOf(work) as credit (creditKey(credit))}
              <button class="actor-credit" draggable="true" title="拖到侧栏筛选"
                ondragstart={(event) => startFilterDrag(event, { kind: "voice", credit })}
                onclick={() => openActor(credit)}>{credit.name}</button>
              <button aria-label={`关注或取消关注 ${credit.name}`} class:active={audioLibrary.isFollowing(credit)}
                onclick={() => audioLibrary.toggle(credit)}>{audioLibrary.isFollowing(credit) ? "已关注" : "关注"}</button>
            {/each}
            {#if !creditsOf(work).length}<span class="hint">声优未知</span>{/if}
          </div>
          <p class="sub">{durationLabel(work.duration_seconds)} · {(work.languages ?? []).join(" / ") || "语言未知"}</p>
          {#if categoriesOf(work).length}
            <FollowTags tags={categoriesOf(work)} />
          {:else}
            <span class="hint">暂无作品标签</span>
          {/if}
          {#if tab === "bedtime"}<p class="reason">{bedtimeReason(work, bedtimeMinutes, prefs.data.tasteProfile, audioLibrary.data.following, bedtimeUnknown)?.reason}</p>{/if}
          {#if (groups.get(work.id) ?? []).some((id) => id !== work.id && (ageProfile !== "all-age" || byId.has(id)))}
            <div class="chips"><span class="hint">官方关联版本：</span>
              {#each (groups.get(work.id) ?? []).filter((id) => id !== work.id && (ageProfile !== "all-age" || byId.has(id))) as id (id)}
                <button onclick={() => officialWork(id)}>{id} {byId.get(id)?.languages?.join("/") || ""}{id === work.original_id ? "（原版）" : ""}</button>
              {/each}
            </div>
          {/if}
        </div>
        <div class="work-actions">
          <QuickFollowButton {work} />
          <label>收听状态 <select value={audioLibrary.data.listening[work.id] ?? ""}
            onchange={(e) => audioLibrary.setListening(work.id, e.currentTarget.value as ListenState | "")}>
            <option value="">未标记</option>{#each Object.entries(LISTEN_LABELS) as [key, label]}<option value={key}>{label}</option>{/each}
          </select></label>
          <button disabled={!work.has_preview} title="打开官方作品页，在页面中使用官方试听" onclick={() => officialWork(work.id)}>官方试听</button>
          {#if !work.duration_seconds}
            <button disabled={detailsBusy} onclick={() => void fillDetails(work.id)}>{work.duration_checked ? "重新查时长" : "查询总时长"}</button>
          {/if}
        </div>
      </article>
    {/each}
    {#if !results.length}<p class="notice" role="status">当前没有匹配作品。可放宽筛选，或先补齐更多作品的声优、语言和时长资料。</p>{/if}
    {#if results.length > maxRows}<button class="more" onclick={() => (maxRows += 40)}>加载更多（剩余 {results.length - maxRows} 部）</button>{/if}
  </div>
</div>

<style>
  .maker-link { background: none; border: 0; padding: 0; color: var(--text); font: inherit; }
  .maker-link:hover, .maker-link:focus-visible { color: var(--accent); text-decoration: underline; }
  .audio-workspace { flex: 1; min-height: 0; overflow: auto; padding: 16px 20px 24px; display: flex; flex-direction: column; gap: 12px; }
  .audio-workspace.embedded { flex: none; overflow: visible; padding: 0; }
  .workspace-title, .toolbar, .actor-search, .results-label { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: flex-start; }
  .workspace-title { justify-content: space-between; }
  h2, h3, h4, p { margin: 0; }
  h2 { font-size: 21px; } h3 { font-size: 16px; } h4 { font-size: 13px; margin-bottom: 6px; }
  .hint, .sub, .results-label { color: var(--muted); font-size: 12px; line-height: 1.5; }
  .grow { flex: 1; }
  button, select, input:not([type="checkbox"]) { border: 1px solid var(--border); color: var(--text); background: var(--panel); border-radius: 7px; min-height: 30px; padding: 5px 8px; font: inherit; font-size: 12px; }
  button { cursor: pointer; } button:hover:not(:disabled), button.active { color: var(--accent); border-color: var(--accent); }
  button:disabled { opacity: .45; cursor: not-allowed; } button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .active { font-weight: 600; }
  .panel, .actors, .notice { border: 1px solid var(--border); background: var(--panel); border-radius: 10px; padding: 12px; }
  .panel { display: flex; flex-direction: column; gap: 10px; }
  .actors summary { cursor: pointer; font-weight: 600; }
  .actor-search { margin: 10px 0; }
  .actor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 6px; }
  .actor { display: flex; gap: 4px; min-width: 0; }
  .actor-name { flex: 1; text-align: left; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .chips { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; }
  .chips button { min-height: 25px; padding: 3px 7px; }
  .chips .actor-credit { cursor: grab; user-select: none; }
  .insights { display: grid; grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); gap: 12px; }
  label { font-size: 12px; display: inline-flex; align-items: center; gap: 5px; flex-wrap: wrap; }
  input[type="number"] { width: 90px; }
  .results-label { justify-content: space-between; }
  .results { display: grid; gap: 8px; }
  .audio-row { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; display: grid; grid-template-columns: 72px minmax(0, 1fr) minmax(124px, auto); align-items: start; gap: 10px; padding: 10px; }
  .work-info { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
  button.work-title { padding: 0; text-align: left; background: none; border: 0; min-height: auto; font-size: 14px; font-weight: 600; overflow-wrap: anywhere; }
  .work-actions { display: flex; flex-direction: column; gap: 6px; }
  .reason { font-size: 12px; color: var(--accent); }
  .more { align-self: center; margin: 8px; }
  @media(max-width: 750px) { .audio-row { grid-template-columns: 72px minmax(0,1fr); } .work-actions { grid-column: 2; flex-direction: row; flex-wrap: wrap; } }
</style>
