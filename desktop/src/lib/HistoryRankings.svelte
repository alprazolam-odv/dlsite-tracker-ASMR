<script lang="ts">
  import { untrack } from "svelte";
  import { loadHistoryRankings, type HistoryRankingWork, type Profile } from "./api";

  let { open, profile, onopen, onclose }: {
    open: boolean;
    profile: Profile;
    onopen: (url: string) => void;
    onclose: () => void;
  } = $props();

  const currentYear = new Date(Date.now() + 9 * 3600000).getUTCFullYear();
  const years = Array.from({ length: currentYear - 1999 }, (_, index) => currentYear - index);
  const number = new Intl.NumberFormat("zh-CN");
  const cache = new Map<string, HistoryRankingWork[]>();
  let dialog: HTMLDialogElement;
  let year = $state(currentYear - 1);
  let period = $state<"annual" | "total">("annual");
  let loading = $state(false);
  let error = $state("");
  let works = $state<HistoryRankingWork[]>([]);
  const selectedYear = $derived(period === "annual" ? year : null);
  const officialUrl = $derived(
    `https://www.dlsite.com/${profile === "all-age" ? "home" : "maniax"}/ranking/${period === "annual" ? "year" : "total"}`
      + `?category=voice&sub=SOU&sort=sale&locale=zh_CN${selectedYear === null ? "" : `&year=${selectedYear}`}`,
  );

  async function load(siteProfile: Profile, chartYear: number | null) {
    if (loading) return;
    error = "";
    const key = `${siteProfile}:${chartYear ?? "total"}`;
    const cached = cache.get(key);
    if (cached) {
      works = cached;
      return;
    }
    works = [];
    loading = true;
    try {
      const result = await loadHistoryRankings(chartYear);
      cache.set(key, result);
      works = result;
    } catch (reason) {
      error = reason instanceof Error ? reason.message : String(reason);
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  });

  $effect(() => {
    if (open) {
      const currentProfile = profile;
      const currentSelection = selectedYear;
      untrack(() => void load(currentProfile, currentSelection));
    }
  });
</script>

<dialog bind:this={dialog} aria-labelledby="history-title" {onclose}>
  <div class="heading">
    <div>
      <h2 id="history-title">历史佳作</h2>
      <p>语音与 ASMR · {profile === "all-age" ? "全年龄区" : "成人区"}</p>
    </div>
    <button class="btn" onclick={() => dialog.close()}>关闭</button>
  </div>

  <div class="controls">
    <div class="choices" role="group" aria-label="榜单类型">
      <button class="btn" class:active={period === "annual"} aria-pressed={period === "annual"}
        disabled={loading} onclick={() => (period = "annual")}>年度榜</button>
      <button class="btn" class:active={period === "total"} aria-pressed={period === "total"}
        disabled={loading} onclick={() => (period = "total")}>历代畅销</button>
    </div>
    {#if period === "annual"}
      <label>年份
        <select bind:value={year} disabled={loading}>
          {#each years as option (option)}
            <option value={option}>{option} 年{option === currentYear ? "（进行中）" : ""}</option>
          {/each}
        </select>
      </label>
    {/if}
    <button class="btn source" onclick={() => onopen(officialUrl)}>在 DLsite 查看</button>
  </div>

  <p class="context">{period === "annual" ? "按所选年份的销量排名，可能包含更早发售的作品。" : "按累计销量排名。"}</p>
  {#if loading}
    <p class="feedback" role="status">正在读取 DLsite 榜单…</p>
  {:else if error}
    <div class="feedback" role="status">
      <p>{error}</p>
      <button class="btn" onclick={() => void load(profile, selectedYear)}>重试</button>
    </div>
  {:else if works.length === 0}
    <p class="feedback" role="status">这个榜单暂无语音或 ASMR 作品。</p>
  {:else}
    {#key selectedYear}
      <div class="chart">
        <table aria-label={selectedYear === null ? "历代畅销" : `${selectedYear} 年度榜`}>
          <thead><tr><th scope="col">排名</th><th scope="col">作品</th><th scope="col" class="sales">{period === "annual" ? "年度销量" : "累计销量"}</th></tr></thead>
          <tbody>
            {#each works as work (work.id)}
              <tr>
                <td class="rank">{work.rank}</td>
                <td>
                  <a href={work.url} onclick={(event) => { event.preventDefault(); onopen(work.url); }}>{work.title}</a>
                  <p>{[work.maker, work.released, work.id].filter(Boolean).join(" · ")}</p>
                </td>
                <td class="sales">{work.sales === null ? "—" : number.format(work.sales)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/key}
  {/if}
</dialog>

<style>
  dialog {
    width: min(760px, calc(100% - 32px));
    max-height: calc(100% - 32px);
    height: min(690px, calc(100% - 32px));
    padding: 20px;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--panel);
    color: var(--text);
    box-shadow: 0 18px 50px rgb(0 0 0 / 35%);
  }
  dialog[open] { display: flex; flex-direction: column; gap: 12px; }
  dialog::backdrop { background: rgb(0 0 0 / 35%); }
  .heading, .controls, .choices, label { display: flex; align-items: center; gap: 8px; }
  .heading { justify-content: space-between; }
  .controls { flex-wrap: wrap; }
  .source { margin-inline-start: auto; }
  h2 { margin: 0 0 4px; font-size: 19px; }
  p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.4; }
  .feedback { display: grid; justify-items: start; gap: 10px; padding: 20px 0; }
  select {
    padding: 6px 8px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    color: var(--text);
    font: inherit;
  }
  .chart { overflow: auto; min-height: 0; }
  table { width: 100%; border-collapse: separate; border-spacing: 0; }
  th, td { text-align: start; padding: 9px 8px; border-bottom: 1px solid var(--border); }
  th { position: sticky; top: 0; background: var(--panel); font-size: 12px; }
  td { overflow-wrap: anywhere; }
  td p { margin-top: 4px; }
  .rank, .sales { font-variant-numeric: tabular-nums; }
  .sales { text-align: end; white-space: nowrap; }
  a { color: var(--text); font-weight: 600; }
  a:hover { color: var(--accent); }
</style>
