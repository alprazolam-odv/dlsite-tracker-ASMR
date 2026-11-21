<script lang="ts">
  import TagChip from "./TagChip.svelte";
  let {
    forms,
    ontap,
  }: {
    forms: string[];
    ontap?: (name: string) => void;
  } = $props();

</script>

<div class="chips">
  {#each forms as name (name)}
    <TagChip
      kind="form"
      text={name}
      title={ontap ? `点击筛选形式「${name}」（再点取消）` : ""}
      onclick={ontap ? () => ontap(name) : undefined}
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
