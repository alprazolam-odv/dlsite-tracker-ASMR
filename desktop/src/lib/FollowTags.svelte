<script lang="ts">
  import { audioLibrary } from "./audio.svelte";
  import TagChip from "./TagChip.svelte";

  let { tags }: { tags: string[] } = $props();
</script>

<div class="tags">
  {#each tags as tag (tag)}
    {@const tracked = audioLibrary.data.followedTags.includes(tag)}
    <TagChip kind="category" text={tag} pressed={tracked} dragFilter ariaLabel={`追踪标签「${tag}」`}
      title={tracked ? `取消追踪「${tag}」` : `追踪「${tag}」的新作`}
      onclick={() => audioLibrary.toggleTag(tag)} />
  {/each}
</div>

<style>
  .tags { display: flex; flex-wrap: wrap; align-items: center; gap: 4px; }
</style>
