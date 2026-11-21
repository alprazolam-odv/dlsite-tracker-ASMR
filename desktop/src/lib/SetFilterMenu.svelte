<script lang="ts">
  // 多选集合菜单（对齐 macOS SetFilterMenu：清除选择 + 勾选列表，触发条显示已选数量）
  import { tick } from "svelte";
  import { ICONS } from "./ui";

  let {
    title,
    emptyLabel,
    options,
    selection,
    hint = "",
    searchable = false,
    labelOf = (option: string) => option,
    onchange,
  }: {
    title: string;
    emptyLabel: string;
    options: string[];
    selection: string[];
    hint?: string;
    searchable?: boolean;
    labelOf?: (option: string) => string;
    onchange: (next: string[]) => void;
  } = $props();

  let open = $state(false);
  let container: HTMLDivElement | null = $state(null);
  let trigger: HTMLButtonElement;
  let searchInput = $state<HTMLInputElement>();
  let query = $state("");
  const resultLimit = 60;
  const matches = $derived.by(() => {
    const keyword = query.trim().toLowerCase();
    return keyword ? options.filter((option) => labelOf(option).toLowerCase().includes(keyword)) : options;
  });
  const shown = $derived(searchable ? matches.slice(0, resultLimit) : matches);

  async function toggleMenu() {
    open = !open;
    if (!open || !searchable) return;
    query = "";
    await tick();
    if (open) searchInput?.focus();
  }

  function toggle(name: string): void {
    onchange(
      selection.includes(name)
        ? selection.filter((item) => item !== name)
        : [...selection, name],
    );
  }

  function onWindowClick(event: MouseEvent): void {
    if (!open || !container) return;
    if (!container.contains(event.target as Node)) open = false;
  }

  function onWindowKeydown(event: KeyboardEvent): void {
    if (event.key !== "Escape" || !open) return;
    open = false;
    if (container?.contains(document.activeElement)) trigger?.focus();
  }
</script>

<svelte:window onclick={onWindowClick} onkeydown={onWindowKeydown} />

<div class="setfilter" bind:this={container}>
  <button class="trigger" bind:this={trigger} title={hint} aria-expanded={open} onclick={toggleMenu}>
    <span class="label">{title}</span>
    <span class="value">{selection.length === 0 ? emptyLabel : `已选 ${selection.length} 项`}</span>
    <span class="chev">{@html ICONS.chevronDown}</span>
  </button>
  {#if open}
    <div class="pop">
      {#if searchable}
        <input type="search" class="search" bind:this={searchInput} bind:value={query}
          placeholder="搜索选项…" aria-label={`搜索${title}`} />
      {/if}
      <button class="header" onclick={() => onchange([])}>清除选择</button>
      <div class="hr"></div>
      <div class="list">
        {#each shown as name (name)}
          <button class="opt" aria-pressed={selection.includes(name)} onclick={() => toggle(name)}>
            <span class="ck" class:on={selection.includes(name)}>
              {#if selection.includes(name)}{@html ICONS.check}{/if}
            </span>
            <span class="nm">{labelOf(name)}</span>
          </button>
        {:else}
          <div class="empty">没有匹配项</div>
        {/each}
      </div>
      {#if searchable && matches.length > resultLimit}
        <div class="empty">显示前 {resultLimit} 项，可继续搜索</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .setfilter {
    position: relative;
  }

  .trigger {
    appearance: none;
    border: 1px solid var(--border);
    background: var(--panel);
    color: var(--text);
    font: inherit;
    font-size: 12.5px;
    border-radius: 8px;
    padding: 5px 8px;
    width: 100%;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: default;
  }

  .trigger:hover {
    border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  }

  .label {
    color: var(--muted);
    flex: none;
  }

  .value {
    flex: 1;
    min-width: 0;
    text-align: right;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .chev {
    display: inline-flex;
    color: var(--muted);
    flex: none;
  }

  .pop {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 200;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 9px;
    box-shadow: 0 10px 26px rgb(0 0 0 / 26%);
    padding: 5px;
    display: flex;
    flex-direction: column;
  }

  .header {
    appearance: none;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 12.5px;
    text-align: left;
    padding: 5px 7px;
    border-radius: 6px;
    cursor: default;
  }

  .header:hover {
    background: color-mix(in srgb, var(--text) 7%, transparent);
  }

  .search {
    width: 100%;
    padding: 5px 7px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
    color: var(--text);
    font: inherit;
    font-size: 12.5px;
  }

  .empty { color: var(--muted); font-size: 12px; padding: 5px 7px; }

  .hr {
    border-top: 1px solid var(--border);
    margin: 3px 4px;
  }

  .list {
    max-height: 320px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }

  .opt {
    appearance: none;
    border: 0;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 12.5px;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 7px;
    border-radius: 6px;
    cursor: default;
    text-align: left;
  }

  .opt:hover {
    background: color-mix(in srgb, var(--text) 7%, transparent);
  }

  .ck {
    display: inline-flex;
    width: 12px;
    justify-content: center;
    color: var(--accent);
    flex: none;
  }

  .nm { overflow-wrap: anywhere; }
</style>
