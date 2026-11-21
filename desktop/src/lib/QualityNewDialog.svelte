<script lang="ts">
  import type { QualityNewOptions, Profile } from "./api";
  let { profile, onsubmit, oncancel }: {
    profile: Profile; onsubmit: (options: QualityNewOptions) => void; oncancel: () => void;
  } = $props();
  const dateText = (offset: number) =>
    new Date(Date.now() + 9 * 3600000 + offset * 86400000).toISOString().slice(0, 10);
  let range = $state<"relative" | "fixed">("relative");
  let days = $state<number | undefined>(30);
  let start = $state(dateText(-29));
  let end = $state(dateText(0));
  let minSales = $state<number | undefined>(100);
  let protectDays = $state<number | undefined>(3);
  let maxWorks = $state<number | undefined>(0);
  const validInt = (value: number | undefined, min: number, max: number) =>
    value !== undefined && Number.isSafeInteger(value) && value >= min && value <= max;
  const valid = $derived(
    (range === "relative" ? validInt(days, 1, 36500) : !!start && !!end && start <= end && end <= dateText(0))
    && validInt(minSales, 0, 4294967295) && validInt(protectDays, 0, 36500) && validInt(maxWorks, 0, 4294967295)
  );
  function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!valid) return;
    onsubmit({
      days: range === "relative" ? days! : null,
      start: range === "fixed" ? start : null, end: range === "fixed" ? end : null,
      min_sales: minSales!, protect_days: protectDays!, max_works: maxWorks!,
    });
  }
</script>

<svelte:window onkeydown={(event) => { if (event.key === "Escape") { event.preventDefault(); oncancel(); } }} />
<div class="overlay">
  <div role="dialog" aria-modal="true" aria-labelledby="quality-title">
  <form class="panel" onsubmit={submit}>
    <h2 id="quality-title">优质新作采集 · {profile === "all-age" ? "全年龄区" : "成人区"}</h2>
    <p>按官方发售日期逐页定位，批量核对销量，再收录命中作品。结果会单独显示，现有作品不会删除。</p>
    <fieldset>
      <legend>发售时间（DLsite 日本时间）</legend>
      <div class="row"><label><input type="radio" bind:group={range} value="relative" /> 最近</label>
        <input aria-label="最近天数" type="number" min="1" max="36500" bind:value={days} disabled={range !== "relative"} /> 天（含今天）</div>
      <div class="row"><label><input type="radio" bind:group={range} value="fixed" /> 指定日期</label></div>
      <div class="dates">
        <label>开始日期 <input type="date" bind:value={start} max={dateText(0)} disabled={range !== "fixed"} /></label>
        <label>结束日期 <input type="date" bind:value={end} max={dateText(0)} disabled={range !== "fixed"} /></label>
      </div>
    </fieldset>
    <label class="row">最低累计销量 <input type="number" min="0" step="1" bind:value={minSales} /> 部</label>
    <p class="hint">设为 0 则不限制销量。</p>
    <label class="row">新作保护 <input type="number" min="0" max="36500" step="1" bind:value={protectDays} /> 天</label>
    <p class="hint">发售距今天不足设定天数的作品，即使销量不足也收录。0 表示关闭。</p>
    <label class="row">最多收录 <input type="number" min="0" step="1" bind:value={maxWorks} /> 部</label>
    <p class="hint">0 表示收录全部命中作品；有限制时按累计销量从高到低选择（保护作品也占数量）。</p>
    {#if !valid}<p class="error" role="status">请输入有效的日期范围及非负整数。</p>{/if}
    <div class="buttons">
      <button class="btn" type="button" onclick={oncancel}>取消</button>
      <button class="btn primary" type="submit" disabled={!valid}>开始采集</button>
    </div>
  </form>
  </div>
</div>
<style>
  .overlay { position: fixed; inset: 0; z-index: 300; background: rgb(0 0 0 / 35%); display: grid; place-items: center; padding: 16px; }
  .panel { width: min(510px, 100%); max-height: 95vh; overflow: auto; display: flex; flex-direction: column; gap: 10px; padding: 20px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; box-shadow: 0 18px 50px rgb(0 0 0 / 35%); }
  h2 { font-size: 18px; margin: 0; }
  p { color: var(--muted); font-size: 12px; line-height: 1.6; margin: 0; }
  fieldset { border: 1px solid var(--border); border-radius: 8px; display: grid; gap: 9px; }
  .row,.dates { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .dates label { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; }
  input:not([type="radio"]) { border: 1px solid var(--border); color: var(--text); background: var(--bg); padding: 7px; border-radius: 6px; min-width: 0; }
  input[type="number"] { width: 100px; }
  label { font-size: 13px; }
  input:disabled { opacity: .5; }
  .hint { margin-top: -7px; }
  .error { color: var(--accent); }
  .buttons { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
</style>
