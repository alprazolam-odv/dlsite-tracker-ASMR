<script lang="ts">
  import { untrack } from "svelte";
  import { externalLibrary } from "./externalLibrary";

  let address = $state(untrack(() => $externalLibrary.endpoint));
  let invalid = $state("");
  function save(event: SubmitEvent) {
    event.preventDefault();
    try {
      void externalLibrary.configure(address);
      address = $externalLibrary.endpoint;
      invalid = "";
    } catch (error) { invalid = (error as Error).message; }
  }
</script>

<form onsubmit={save}>
  <label for="external-library-url">外部作品库接口</label>
  <input id="external-library-url" type="text" inputmode="url" bind:value={address}
    autocomplete="off" spellcheck="false" placeholder="输入接口地址，留空关闭"
    aria-invalid={!!invalid} aria-describedby="library-help" oninput={() => (invalid = "")} />
  <small id="library-help">保存后会查询当前模式的 RJ 编号。可在列表上方切换显示已在库和已隐藏的作品。</small>
  {#if invalid}<small role="alert">{invalid}</small>{/if}
  <div class="buttons">
    <button class="btn" disabled={address === $externalLibrary.endpoint}>保存地址</button>
    {#if $externalLibrary.endpoint}
      <button class="btn" type="button" disabled={$externalLibrary.syncing || address !== $externalLibrary.endpoint}
        onclick={() => void externalLibrary.refresh()}>{$externalLibrary.syncing ? "同步中…" : "立即刷新"}</button>
    {/if}
  </div>
  {#if $externalLibrary.endpoint}
    <small role="status">
      {#if $externalLibrary.syncing}正在查询作品库…
      {:else if $externalLibrary.syncedAt}上次同步 {new Date($externalLibrary.syncedAt).toLocaleString("zh-CN")}
      {:else if !$externalLibrary.error}等待读取作品列表
      {/if}
    </small>
  {/if}
</form>

<style>
  form { display: grid; gap: 8px; }
  label { display: flex; align-items: center; gap: 6px; font-size: 13px; }
  input[type="text"] { min-width: 0; width: 100%; padding: 6px 8px; border: 1px solid var(--border);
    border-radius: 6px; background: var(--bg); color: var(--text); font: inherit; }
  small { color: var(--muted); font-size: 12px; }
  .buttons { display: flex; gap: 8px; }
</style>
