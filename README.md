# 同人音声雷达 · DLsite Tracker ASMR

一个在本机运行的 DLsite 同人音声浏览工具，从 [Faintimi/dlsite-tracker](https://github.com/Faintimi/dlsite-tracker) 的同人游戏雷达改造而来。

默认追踪 DLsite 同人成人区（`maniax`）中的音声／ASMR 作品（`SOU`），范围不含音乐、游戏和其他作品类型。项目读取公开作品资料、销量、评分、榜单与封面；音频试听、购买和下载请前往 DLsite 原作品页。

顶部可以切换到独立的全年龄模式（`home`，仅官方明确标为全年龄的 `SOU`）。两个模式各自初始化、更新、保存作品库、收藏、声优和社团的关注以及收听记录，切换时程序会重新启动，已有成人区数据不会删除。

## 功能

- 查看音声日榜、周榜和月榜，或按发售日期逐步导入历史作品。
- 按作品名、社团或声优搜索，组合标签、发售年份、评分、销量与价格筛选。
- 使用收藏夹和标签偏好整理作品。收藏与设置保存在本机。
- 点作品上的「＋关注」，在同一面板里点选声优、社团和作品标签。带勾表示已关注，再点可取消，选择立即保存。
- 从侧栏「我的关注」进入，侧栏收起时入口在顶栏。「关注清单」分组列出所有已关注的声优、社团和标签，可以按名称搜索、取消关注或添加标签。
- 「新作动态」按声优、社团、标签显示近 14 天发售且已入库的作品，各页独立标记已读。追踪的任一标签命中即可进入「标签新作」。作品下方显示原始标签，可直接点选追踪。「检查新作」会启动热榜快更。
- 点作品卡片的声优名可打开主页，也可以从「关注清单」进入「声优目录」，筛选多位声优的合作作品、查看合作关系或使用睡前推荐。这里保留音声主题、语言、时长、收听状态、试听和本地作品筛选，也可切换原作与译版合并。
- 睡前推荐结合明确的音声标签、已知时长、口味偏好和关注声优。没有可靠时长的作品可以作为标明「时长未知」的备选，不视作符合设定时间。利用「补齐音声资料（10 部）」可分批补齐旧库资料和官方作品页明示的总时长，也可在单部作品旁查询。没有统一时长字段的作品仍显示未知，不估算。
- 本地音频识别需要用户明确选择目录，只扫描文件名和祖先目录中的 RJ 编号；仅在应用本地存储识别结果，不上传音频、文件路径或收听记录。识别记录可清除，不会删除原文件。
- 官方试听按钮打开 DLsite 的作品页面，使用站点提供的试听功能。
- 「开始更新数据」→「优质新作采集」可设定最近天数或起止日期、最低累计销量、新作保护天数以及收录上限。默认最近 30 天、最低 100 部销量、保护 3 天、数量不限；仅对命中的新作品补齐详情。完成后点击「查看本次采集」按销量浏览结果，原有作品不会被删除。

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
