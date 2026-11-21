<script lang="ts">
  import type { Credit } from "./audio";
  import { creditKey } from "./audio";
  import { audioLibrary } from "./audio.svelte";
  import { library, type FollowedMaker } from "./library.svelte";
  import FollowTags from "./FollowTags.svelte";

  let { tagOptions, onvoice, onmaker, onfindvoices }: {
    tagOptions: string[];
    onvoice: (credit: Credit) => void;
    onmaker: (maker: FollowedMaker) => void;
    onfindvoices: () => void;
  } = $props();

  let query = $state("");
  let newTag = $state("");
  const search = $derived(query.trim().toLocaleLowerCase());
  const voices = $derived(audioLibrary.data.following.filter((v) => v.name.toLocaleLowerCase().includes(search)));
  const circles = $derived(library.data.makers.filter((m) => m.name.toLocaleLowerCase().includes(search)));
  const tags = $derived(audioLibrary.data.followedTags.filter((name) => name.toLocaleLowerCase().includes(search)));
  const tag = $derived(newTag.trim());
  const tracked = $derived(audioLibrary.data.followedTags.includes(tag));
  function addTag(event: SubmitEvent) {
    event.preventDefault();
    if (!tag || tracked) return;
    audioLibrary.toggleTag(tag);
    newTag = "";
    query = "";
  }
</script>

<label class="search">查找已关注 <input type="search" bind:value={query} placeholder="声优、社团或标签" /></label>
<section>
  <header><h3>声优 <small>{audioLibrary.data.following.length}</small></h3><button class="btn" onclick={onfindvoices}>声优目录</button></header>
  <ul>
    {#each voices as voice (creditKey(voice))}
      <li><button class="name" onclick={() => onvoice(voice)}>{voice.name}</button>
        <button class="remove" aria-label={`取消关注声优 ${voice.name}`} onclick={() => audioLibrary.toggle(voice)}>取消关注</button></li>
    {:else}<li class="empty">{search ? "没有匹配的声优" : "还没有关注声优"}</li>{/each}
  </ul>
</section>
<section>
  <header><h3>社团 <small>{library.data.makers.length}</small></h3></header>
  <ul>
    {#each circles as maker (maker.key)}
      <li><button class="name" onclick={() => onmaker(maker)}>{maker.name}</button>
        <button class="remove" aria-label={`取消关注社团 ${maker.name}`} onclick={() => library.toggleFollow(maker.key, maker.name, maker.maker_id)}>取消关注</button></li>
    {:else}<li class="empty">{search ? "没有匹配的社团" : "还没有关注社团"}</li>{/each}
  </ul>
</section>
<section>
  <header><h3>标签 <small>{audioLibrary.data.followedTags.length}</small></h3></header>
  {#if tags.length}<FollowTags {tags} />
  {:else}<p class="empty">{search ? "没有匹配的标签" : "还没有追踪标签"}</p>{/if}
  <form onsubmit={addTag}>
    <input list="follow-tag-options" aria-label="要追踪的标签" placeholder="输入或选择标签" bind:value={newTag} />
    <datalist id="follow-tag-options">{#each tagOptions as name (name)}<option value={name}></option>{/each}</datalist>
    <button class="btn" disabled={!tag || tracked}>{tracked ? "已追踪" : "追踪标签"}</button>
  </form>
</section>

<style>
  .search, header, form, li { display: flex; align-items: center; gap: 8px; }
  .search, form { flex-wrap: wrap; }
  input { padding: 6px 9px; background: var(--panel); color: var(--text); border: 1px solid var(--border); border-radius: 6px; }
  section { padding: 14px 0; border-bottom: 1px solid var(--border); }
  header { margin-bottom: 8px; }
  h3, p, ul { margin: 0; }
  h3 { font-size: 15px; }
  ul { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 5px 20px; list-style: none; padding: 0; }
  li { justify-content: space-between; }
  .name, .remove { background: none; border: 0; color: var(--text); cursor: pointer; padding: 4px 0; font: inherit; text-align: left; overflow-wrap: anywhere; }
  .remove, .empty, small { color: var(--muted); font-size: 12px; }
  .remove { flex: none; }
  .name:hover, .remove:hover { color: var(--accent); text-decoration: underline; }
  form { margin-top: 12px; }
  :is(button, input):focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
