<script lang="ts">
  import { onMount } from "svelte";
  import { loadCreatorWorks, type CatalogCreator, type CreatorWorksPage, type WorkView } from "./api";
  import Cover from "./Cover.svelte";
  import ExternalLibraryFilters from "./ExternalLibraryFilters.svelte";
  import { externalLibrary, libraryKey, visibleLibraryWorks, type LibraryMarks } from "./externalLibrary";

  let { creator, works, onopen, onlocal, onclose }: {
    creator: CatalogCreator;
    works: WorkView[];
    onopen: (url: string) => void;
    onlocal: () => void;
    onclose: () => void;
  } = $props();

  let dialog: HTMLDialogElement;
  let list: HTMLDivElement;
  let mounted = false;
  const cache = new Map<number, CreatorWorksPage>();
  let page = $state(1);
  let loadingPage = $state(0);
  let failedPage = $state(0);
  let result = $state.raw<CreatorWorksPage | null>(null);
  let error = $state("");
  let pageMarks = $state.raw<LibraryMarks | undefined>(undefined);
  let checking = $state(false);
  let lookupError = $state("");
  let lookupAttempts = $state(0);
  const localWorks = $derived(new Map(works.map(work => [libraryKey(work.id), work])));
  const endpoint = $derived($externalLibrary.endpoint);
  const marks = $derived(pageMarks ?? $externalLibrary.marks);
  const visible = $derived(visibleLibraryWorks(result?.works ?? [], { ...$externalLibrary, marks }));
  const waitingForFilter = $derived(checking && ($externalLibrary.hideCollected || $externalLibrary.hideExcluded));

  async function load(nextPage: number) {
    if (loadingPage) return;
    failedPage = 0;
    error = "";
    loadingPage = nextPage;
    try {
      const next = cache.get(nextPage) ?? await loadCreatorWorks(creator, nextPage);
      if (!mounted) return;
      cache.set(nextPage, next);
      page = nextPage;
      result = next;
      list.scrollTop = 0;
    } catch (err) {
      if (!mounted) return;
      error = String(err).replace(/^Error: /, "");
      failedPage = nextPage;
    } finally {
      if (mounted) loadingPage = 0;
    }
  }

  onMount(() => {
    mounted = true;
    dialog.showModal();
    void load(1);
    return () => { mounted = false; };
  });

  $effect(() => {
    const currentPage = result;
    const address = endpoint;
    void lookupAttempts;
    pageMarks = undefined;
    lookupError = "";
    checking = false;
    if (!address || !currentPage?.works.length) return;
    const controller = new AbortController();
    let current = true;
    checking = true;
    void externalLibrary.lookupPage(currentPage.works, controller).then(
      checked => { if (current) pageMarks = checked; },
      () => { if (current) lookupError = "音声库查询失败，当前页使用已有标记。"; },
    ).finally(() => {
      if (current) checking = false;
    });
    return () => {
      current = false;
      controller.abort();
    };
  });
</script>

<dialog bind:this={dialog} aria-labelledby="creator-title" {onclose}>
  <header>
    <div>
      <h2 id="creator-title">{creator.name}</h2>
      <p>DLsite {creator.kind === "voice" ? "声优" : "社团"}音声作品</p>
    </div>
    <button class="btn" onclick={() => dialog.close()}>关闭</button>
  </header>
  <div class="toolbar">
    <ExternalLibraryFilters />
    <button class="btn local" onclick={onlocal}>在雷达已导入作品中筛选</button>
  </div>
  {#if checking}<p role="status">正在查询这一页的音声库状态…</p>{/if}
  {#if lookupError}
    <div class="feedback" role="status">
      <span>{lookupError}</span><button class="btn" onclick={() => (lookupAttempts += 1)}>重查音声库</button>
    </div>
  {/if}
  {#if loadingPage}<p role="status">正在从 DLsite 加载第 {loadingPage} 页…</p>{/if}
  {#if failedPage}
    <div class="feedback" role="status">
      <span>{error || "DLsite 目录读取失败。"}</span>
      <button class="btn" onclick={() => void load(failedPage)}>重试第 {failedPage} 页</button>
    </div>
  {/if}

  <div class="works" bind:this={list}>
    {#if result && !waitingForFilter}
      {#each visible as work (work.id)}
        {@const localWork = localWorks.get(libraryKey(work.id))}
        <article>
          <Cover workId={work.id} src={localWork?._cover || work.cover} libraryMarks={marks} width={96} height={72} rounded />
          <div>
            <a href={work.url} onclick={(event) => { event.preventDefault(); onopen(work.url); }}>{work.title}</a>
            <p>{[work.maker, localWork?.regist_date?.slice(0, 10), work.id].filter(Boolean).join(" · ")}</p>
            {#if !localWork}<p>未导入雷达</p>{/if}
          </div>
        </article>
      {:else}
        <p class="empty">{result.works.length ? "这一页的作品已被当前音声库筛选隐藏。" :
          result.has_more || page > 1 ? "这一页没有符合条件的音声作品。" : "DLsite 暂无符合条件的音声作品。"}</p>
      {/each}
    {/if}
  </div>

  {#if result}
    <footer>
      <p>第 {page} 页{waitingForFilter ? "" : ` · 显示 ${visible.length} / ${result.works.length} 部`}</p>
      <button class="btn" disabled={page === 1 || !!loadingPage} onclick={() => void load(page - 1)}>上一页</button>
      <button class="btn" disabled={!result.has_more || !!loadingPage} onclick={() => void load(page + 1)}>下一页</button>
    </footer>
  {/if}
</dialog>

<style>
  dialog {
    width: min(780px, calc(100% - 40px));
    height: min(710px, calc(100% - 40px));
    padding: 18px;
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--panel);
    color: var(--text);
  }
  dialog[open] { display: flex; flex-direction: column; gap: 10px; }
  dialog::backdrop { background: rgb(0 0 0 / 35%); }
  header, .toolbar, footer, .feedback { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
  header { justify-content: space-between; }
  .local { margin-inline-start: auto; }
  h2 { margin: 0 0 4px; font-size: 20px; }
  p { margin: 0; color: var(--muted); font-size: 13px; }
  .works { flex: 1; min-height: 0; overflow: auto; border-block: 1px solid var(--border); }
  article { display: flex; align-items: center; gap: 12px; padding: 9px 4px; border-bottom: 1px solid var(--border); }
  article p { margin-top: 4px; }
  a { color: var(--text); font-weight: 600; overflow-wrap: anywhere; }
  a:hover, a:focus-visible { color: var(--accent); }
  .empty { padding: 16px 4px; }
  footer p { margin-inline-end: auto; }
</style>
