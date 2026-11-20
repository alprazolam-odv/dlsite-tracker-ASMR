# 同人音声雷达 · DLsite Tracker ASMR

一个在本机运行的 DLsite 同人音声浏览工具，从 [Faintimi/dlsite-tracker](https://github.com/Faintimi/dlsite-tracker) 的同人游戏雷达改造而来。

默认追踪 DLsite 同人成人区（`maniax`）中的音声／ASMR 作品（`SOU`），范围不含音乐、游戏和其他作品类型。项目读取公开作品资料、销量、评分、榜单与封面；音频试听、购买和下载请前往 DLsite 原作品页。

## 功能

- 查看音声日榜、周榜和月榜，或按发售日期逐步导入历史作品。
- 按作品名、社团或声优搜索，组合标签、发售年份、评分、销量与价格筛选。
- 使用收藏夹、标签偏好和社团关注来整理作品。收藏与设置保存在本机。
- 作品卡片显示声优，点击姓名进入声优主页；在「音声工作台」可同时选择多个声优、关注声优、查看近 14 天的已入库新作及合作社团/声优、相近标签的声优。
- 音声工作台支持耳语、采耳、双耳录音等主题，官方语言/版本、播放时长、想听/已听/不喜欢、试听信息和本地已有作品筛选。原作与译版按官方关联去重，可关闭合并查看每个版本。
- 睡前推荐结合明确的音声标签、已知时长、口味偏好和关注声优。没有可靠时长的作品不会进入时长推荐。利用「补齐音声资料（10 部）」可分批补齐旧库资料和官方作品页明示的总时长，也可在单部作品旁查询。没有统一时长字段的作品仍显示未知，不估算。
- 本地音频识别需要用户明确选择目录，只扫描文件名和祖先目录中的 RJ 编号；仅在应用本地存储识别结果，不上传音频、文件路径或收听记录。识别记录可清除，不会删除原文件。
- 官方试听按钮打开 DLsite 的作品页面，使用站点提供的试听功能。

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
python -m dlsite_tracker import-recent --years 1
python -m dlsite_tracker export
```

`out/` 中包含 `works.json`、`works.csv` 与本地封面。历史导入依据官方发售日期判断范围，遇到日期缺失时保留候选；默认不按销量排除旧作。

## 来源与许可

仅使用公开商品资料，无需 DLsite 账号，采集保留站点的 robots 规则和限速。本项目与 DLsite 无官方关联，沿用上游 [MIT 许可](LICENSE)。

[English](README_EN.md)
