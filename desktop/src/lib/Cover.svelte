<script lang="ts">
  import { ICONS } from "$lib/ui";
  import { externalLibrary, libraryKey, type LibraryMarks } from "./externalLibrary";
  import { prefs } from "$lib/prefs.svelte";

  let {
    src,
    workId,
    width,
    height,
    rounded = false,
    libraryMarks,
  }: {
    src?: string;
    workId: string;
    width?: number | string;
    height?: number | string;
    rounded?: boolean;
    libraryMarks?: LibraryMarks;
  } = $props();

  const key = $derived(libraryKey(workId));
  const marks = $derived(libraryMarks ?? $externalLibrary.marks);
  const collected = $derived(marks.collected.has(key));
  const excluded = $derived(marks.excluded.has(key));
  const unknown = $derived(marks.unknown.has(key));

  const style = $derived(
    `${width !== undefined ? `width:${typeof width === "number" ? `${width}px` : width};` : ""}` +
      `${height !== undefined ? `height:${typeof height === "number" ? `${height}px` : height};` : ""}`,
  );
</script>

<div class="cover" class:rounded class:private={prefs.data.hideImages}
  class:marked={collected || excluded || unknown} style={style}>
  {#if prefs.data.hideImages}
    <span class="privacy-label">封面隐藏</span>
  {:else if src}
    <img src={src} alt="" loading="lazy" decoding="async" />
  {:else}
    <span class="fallback">{@html ICONS.gamepad}</span>
  {/if}
  {#if collected || excluded || unknown}
    <div class="library-marks">
      {#if collected}<span title={unknown ? "上次已在库，本次待确认" : "音声库中已有此作品"}>已在库</span>{/if}
      {#if excluded}<span title="在音声库中标记为整部排除">已隐藏</span>{/if}
      {#if unknown && !collected}<span title="本次未能确认是否收录">待确认</span>{/if}
    </div>
  {/if}
</div>

<style>
  .library-marks {
    position: absolute;
    bottom: 3px;
    left: 3px;
    right: 3px;
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
  }
  .library-marks span {
    padding: 1px 3px;
    border-radius: 3px;
    background: var(--panel);
    color: var(--text);
    border: 1px solid var(--border);
    font-size: 11px;
    line-height: 1.3;
    white-space: nowrap;
  }
  .cover {
    position: relative;
    flex: none;
    overflow: hidden;
    background: linear-gradient(135deg, #4a3873 0%, #21304d 100%);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .cover.rounded {
    border-radius: 9px;
  }

  .cover.private {
    background: var(--coverbg);
  }

  .privacy-label {
    color: var(--muted);
    font-size: 10px;
    white-space: nowrap;
  }

  .private.marked .privacy-label {
    align-self: flex-start;
    margin-top: 5px;
  }

  .cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .fallback {
    color: rgb(255 255 255 / 65%);
    display: flex;
  }
</style>
