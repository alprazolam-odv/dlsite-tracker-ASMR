<script lang="ts">
  import { externalLibrary } from "./externalLibrary";
</script>

{#if $externalLibrary.endpoint}
  <div class="library-filters" role="group" aria-label="音声库作品筛选">
    <span>音声库</span>
    <label title="显示音声库中已有的作品">
      <input type="checkbox" checked={!$externalLibrary.hideCollected}
        onchange={(event) => externalLibrary.setFilter("hideCollected", !event.currentTarget.checked)} />
      显示已在库
    </label>
    <label title="显示在音声库里标为整部排除的作品">
      <input type="checkbox" checked={!$externalLibrary.hideExcluded}
        onchange={(event) => externalLibrary.setFilter("hideExcluded", !event.currentTarget.checked)} />
      显示已隐藏
    </label>
  </div>
{/if}

<style>
  .library-filters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 14px;
    color: var(--muted);
    font-size: 13px;
  }
  label {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-height: 28px;
    color: var(--text);
    cursor: pointer;
  }
</style>
