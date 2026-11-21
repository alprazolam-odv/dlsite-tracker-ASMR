# DLsite Tracker ASMR

A local desktop browser for DLsite doujin voice and ASMR works, adapted from [Faintimi/dlsite-tracker](https://github.com/Faintimi/dlsite-tracker). It uses the `maniax` voice scope (`SOU`) by default and keeps its library separate from the game edition.

Browse voice rankings and older releases, search and follow credited voice actors, filter by language, ASMR themes, explicitly stated duration and listening state, and group official translations. The voice directory under Following also includes related actors, bedtime suggestions and an optional local RJ audio-file scan. The scan keeps files and paths on your device. Works with no reliable total running time show an unknown duration. Official previews and purchases are on DLsite.

Drag a work's tag or voice actor to the left sidebar to filter the local work list. Drop a tag on **排除标签** (Exclude Tags) to hide works with that tag. Results must match every selected tag and voice actor. You can also search and select filters in the sidebar or remove them above the results.

Select **＋关注** on a work to follow any of its credited actors, publishing circle or original tags. In **我的关注** (Following), open **关注清单** to see, search or remove all your follows. **新作动态** shows releases from the past 14 days in your current library. The actor, circle and tag feeds have independent read states. Select a tag on a feed card to toggle tracking. When the sidebar is hidden, use **我的关注** in the top bar.

See the [Chinese README](README.md) for build and usage instructions. The project is [MIT licensed](LICENSE) and is not affiliated with DLsite.

The desktop app also offers a separate all-age mode with its own database, preferences and favorites, plus a configurable recent-release collector with a release date range, minimum cumulative sales, new-release grace period and optional result limit.

Open **历史佳作** (Historical Rankings) next to **优质新作** (Recent Picks) for the official voice and ASMR sales charts in the current profile. The previous complete year opens by default. Select another year or switch to all-time bestsellers. Browsing a chart does not import its works.

Radar imports the current profile's officially credited voice works for followed actors in the background, including actors you followed before updating. Their names open the local catalog. In **声优新作** (Actor Releases), **检查新作** (Check for New Releases) scans the latest results up to the previously covered catalog and imports newly found titles. Works are deduplicated by RJ number and stay in the local catalog when you unfollow an actor. Circle and tag release checks continue to use the quick chart refresh.

Select an unfollowed actor or a publishing circle to browse DLsite's voice catalog for the current age profile in Radar, one page at a time. The cover wall offers the same actions in the right-click menu. The online list includes translations and works you have yet to import. Actors use DLsite's creator-name search, while circles use the official ID when available. The library visibility controls check only the current online page. Select **在雷达已导入作品中筛选** to browse the local catalog.

An optional external library can mark works as **已在库** (In Library), **已隐藏** (Hidden in the external library), or both. If the library has any edition that DLsite explicitly links to a work, the linked editions share the In Library badge and filter. Hidden status applies to each RJ ID independently. In the desktop app, open **个性化** (Personalization), enter the lookup URL under **外部作品库接口**, and save it. Use the two checkboxes above the work list to show or hide each group. Both are shown by default. Each profile keeps its settings and last results locally. It syncs at startup, supports manual refresh, and keeps the last marks with a warning if the service is offline. See the [JSON lookup protocol](README.md#可选的外部作品库) to connect a compatible service.
