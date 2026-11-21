<script module lang="ts">
  import { createContext } from "svelte";
  import type { WorkView } from "./api";
  const [getQuickFollow, setQuickFollow] = createContext<(work: WorkView) => void>();
  export { setQuickFollow };
</script>

<script lang="ts">
  let { work }: { work: WorkView } = $props();
  const open = getQuickFollow();
</script>

<button class="quick" aria-haspopup="dialog" title="关注这部作品的声优、社团或标签"
  onclick={(event) => { event.stopPropagation(); open(work); }}
  ondblclick={(event) => event.stopPropagation()}>＋关注</button>

<style>
  .quick { flex: none; width: fit-content; border: 1px solid var(--border); border-radius: 6px; padding: 3px 7px; background: var(--panel); color: var(--text); font: inherit; font-size: 12px; cursor: pointer; }
  .quick:hover, .quick:focus-visible { border-color: var(--accent); }
</style>
