<script lang="ts">
  import TagChip from "./TagChip.svelte";
  let {
    categories,
    ontap,
    onmenu,
  }: {
    categories: string[];
    ontap?: (name: string) => void;
    onmenu?: (name: string, event: MouseEvent) => void;
  } = $props();

</script>

<div class="chips">
  {#each categories as name (name)}
    <TagChip
      kind="category"
      text={name}
      dragFilter={!!ontap}
      title={onmenu ? "" : ontap ? `点击筛选分类「${name}」（再点取消）` : ""}
      onclick={ontap ? () => ontap(name) : undefined}
      oncontextmenu={onmenu ? (event) => onmenu(name, event) : undefined}
    />
  {/each}
</div>

<style>
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    min-width: 0;
  }

</style>
