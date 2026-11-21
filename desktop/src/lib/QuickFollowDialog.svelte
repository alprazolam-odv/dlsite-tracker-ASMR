<script lang="ts">
  import { onMount } from "svelte";
  import type { WorkView } from "./api";
  import { creditKey, creditsOf } from "./audio";
  import { audioLibrary } from "./audio.svelte";
  import { makerKeyOf } from "./filter";
  import { library } from "./library.svelte";
  import { categoriesOf } from "./ui";
  import FollowTags from "./FollowTags.svelte";
  import TagChip from "./TagChip.svelte";

  let { work, onclose }: { work: WorkView; onclose: () => void } = $props();
  let dialog: HTMLDialogElement;
  onMount(() => { dialog.showModal(); });
  const makerKey = $derived(makerKeyOf(work.maker, work.maker_id));
  const tags = $derived(categoriesOf(work));
</script>

<dialog bind:this={dialog} aria-labelledby="quick-follow-title" {onclose}>
  <header><h2 id="quick-follow-title">快速关注</h2><button class="btn" onclick={() => dialog.close()}>完成</button></header>
  <p>{work.title}</p>
  <h3>声优</h3>
  <div class="choices">
    {#each creditsOf(work) as credit (creditKey(credit))}
      <TagChip kind="category" text={credit.name} pressed={audioLibrary.isFollowing(credit)}
        ariaLabel={`关注声优「${credit.name}」`} onclick={() => audioLibrary.toggle(credit)} />
    {:else}<span>暂无声优署名</span>{/each}
  </div>
  <h3>社团</h3>
  {#if work.maker}
    <TagChip kind="category" text={work.maker} pressed={library.isFollowing(makerKey)}
      ariaLabel={`关注社团「${work.maker}」`} onclick={() => library.toggleFollow(makerKey, work.maker, work.maker_id ?? "")} />
  {:else}<span>暂无社团资料</span>{/if}
  <h3>标签</h3>
  {#if tags.length}<FollowTags {tags} />{:else}<span>暂无作品标签</span>{/if}
</dialog>

<style>
  dialog { width: min(440px, 85vw); max-height: 80vh; overflow: auto; box-sizing: border-box; padding: 20px; border: 1px solid var(--border); border-radius: 12px; background: var(--panel); color: var(--text); }
  dialog::backdrop { background: rgb(0 0 0 / 35%); }
  header, .choices { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
  header { justify-content: space-between; }
  h2, h3, p { margin: 0; }
  h2 { font-size: 18px; }
  h3 { font-size: 13px; margin: 16px 0 6px; }
  p, span { font-size: 12px; color: var(--muted); }
  p { margin-top: 6px; overflow-wrap: anywhere; }
</style>
