# 同人音声雷达 · DLsite Tracker ASMR

一个在本机运行的 DLsite 同人音声浏览工具，从 [Faintimi/dlsite-tracker](https://github.com/Faintimi/dlsite-tracker) 的同人游戏雷达改造而来。

默认追踪 DLsite 同人成人区（`maniax`）中的音声／ASMR 作品（`SOU`），范围不含音乐、游戏和其他作品类型。项目读取公开作品资料、销量、评分、榜单与封面；音频试听、购买和下载请前往 DLsite 原作品页。

顶部可以切换到独立的全年龄模式（`home`，仅官方明确标为全年龄的 `SOU`）。两个模式各自初始化、更新、保存作品库、收藏、声优关注和收听记录，切换时程序会重新启动，已有成人区数据不会删除。

## 功能

- 查看音声日榜、周榜和月榜，或按发售日期逐步导入历史作品。
- 按作品名、社团或声优搜索，组合标签、发售年份、评分、销量与价格筛选。
- 使用收藏夹、标签偏好和社团关注来整理作品。收藏与设置保存在本机。
- 作品卡片显示声优，点击姓名进入声优主页；在「音声工作台」可同时选择多个声优、关注声优、查看近 14 天的已入库新作及合作社团/声优、相近标签的声优。
- 音声工作台支持耳语、采耳、双耳录音等主题，官方语言/版本、播放时长、想听/已听/不喜欢、试听信息和本地已有作品筛选。原作与译版按官方关联去重，可关闭合并查看每个版本。
- 睡前推荐结合明确的音声标签、已知时长、口味偏好和关注声优。没有可靠时长的作品可以作为标明「时长未知」的备选，不视作符合设定时间。利用「补齐音声资料（10 部）」可分批补齐旧库资料和官方作品页明示的总时长，也可在单部作品旁查询。没有统一时长字段的作品仍显示未知，不估算。
- 本地音频识别需要用户明确选择目录，只扫描文件名和祖先目录中的 RJ 编号；仅在应用本地存储识别结果，不上传音频、文件路径或收听记录。识别记录可清除，不会删除原文件。
- 官方试听按钮打开 DLsite 的作品页面，使用站点提供的试听功能。
- 「开始更新数据」→「优质新作采集」可设定最近天数或起止日期、最低累计销量、新作保护天数以及收录上限。默认最近 30 天、最低 100 部销量、保护 3 天、数量不限；仅对命中的新作品补齐详情。完成后点击「查看本次采集」按销量浏览结果，原有作品不会被删除。

## 可选的外部作品库

在桌面版「个性化 → 外部作品库接口」填写查库地址，点击「保存地址」。雷达会在打开作品列表时自动同步，也可以点击「立即刷新」。封面可同时显示「已收录」和「已排除」，两个隐藏开关可单独使用。服务离线时沿用上次结果并提示可能过期。清空地址并保存即可关闭。成人区和全年龄模式分别在应用本地保存地址、筛选偏好和标记。

可以连接 AutoWatcher（本机默认查库地址为 `http://127.0.0.1:18923/check-library`）或实现下述协议的服务。仅向用户配置的地址发送当前模式作品的 RJ 编号。接口需支持跨域 JSON POST 和 OPTIONS 预检。

请求示例（每批最多 5000 个编号）：

```json
{"action":"check_library","rjs":["RJ000101","RJ000102","RJ000103"]}
```

响应示例：

```json
{"complete":true,"collected":["RJ000101"],"absent":["RJ000102","RJ000103"],"unknown":[],"excluded":["RJ000101","RJ000102"]}
```

每个编号应恰好出现在 `collected`（已收录）、`absent`（确认未收录）或 `unknown`（本次无法确认）之一。`excluded` 独立表示整部作品已排除。无法检查全部目录时返回 `complete: false`，未能判定的作品放入 `unknown`，雷达保留其上次确认的收录标记。服务可选返回字符串 `snapshot`，雷达在同一次同步的下一批请求中原样带回，以便复用目录扫描。不同批次全部成功后才替换本机缓存。

## 从源码构建桌面版

需要 Node.js（LTS）、Rust 和 Python 3.9 以上；Windows 另需 WebView2 和 Visual Studio C++ Build Tools，macOS 需要 Xcode 命令行工具。Windows 请用 Git Bash 执行打包脚本。

```bash
git clone https://github.com/alprazolam-odv/dlsite-tracker-ASMR.git
cd dlsite-tracker-ASMR
bash scripts/build-sidecar.sh
cd desktop
npm ci
npm run tauri build
```

构建产物在 `desktop/src-tauri/target/release/bundle/`。首次打开点「初始化数据」，应用会从音声榜建立作品库。想浏览更多旧作，可从更新菜单启动历史导入；所需时间取决于导入范围和站点限速。

音声版使用独立的数据目录，不会自动接管游戏版数据库。Windows 默认作品库位于 `%APPDATA%\com.faintimi.doujin-audio-radar\pipeline\`。如需手动选择数据文件，请使用本项目导出的音声 `works.json`。

数据采集自动使用 Windows 系统代理或环境变量（`HTTP_PROXY`、`HTTPS_PROXY`），支持 HTTP/混合代理端口。如果没有代理设置，则直接联网。

## 命令行

仅运行数据管道时只需 Python 3.9 以上，无需安装运行依赖。在仓库根目录把 `config.example.ini` 复制为 `config.ini`，再执行：

```bash
python -m dlsite_tracker init
python -m dlsite_tracker task quick
python -m dlsite_tracker quality-new --days 30 --min-sales 100 --protect-days 3
python -m dlsite_tracker import-recent --years 1
python -m dlsite_tracker export
```

`out/` 中包含 `works.json`、`works.csv` 与本地封面。历史导入依据官方发售日期判断范围，遇到日期缺失时保留候选；默认不按销量排除旧作。

优质新作也支持 `--start YYYY-MM-DD --end YYYY-MM-DD` 替代 `--days`，以及 `--max-works N`（0 不限）。按 DLsite 日本日期计算，包含起止两天；保护从当天向前计算，不等同于 30 天内累计销量。日期未知或超出范围的作品不会进入本次结果。

## 来源与许可

仅使用公开商品资料，无需 DLsite 账号，采集保留站点的 robots 规则和限速。本项目与 DLsite 无官方关联，沿用上游 [MIT 许可](LICENSE)。

[English](README_EN.md)
