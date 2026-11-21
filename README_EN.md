# DLsite Tracker ASMR

A local desktop browser for DLsite doujin voice and ASMR works, adapted from [Faintimi/dlsite-tracker](https://github.com/Faintimi/dlsite-tracker). It uses the `maniax` voice scope (`SOU`) by default and keeps its library separate from the game edition.

Browse voice rankings and older releases, search and follow credited voice actors, filter by language, ASMR themes, explicitly stated duration and listening state, and group official translations. The audio workspace also includes related actors, bedtime suggestions and an optional local RJ audio-file scan. It stores listening preferences and matched identifiers locally; the scan does not upload files or paths. Some products have no reliable total running time; those remain unknown. Official previews and purchases are on DLsite.

The sidebar's **我的关注** (Following) section has separate feeds and subscription lists for voice actors and publishing circles. Each feed shows releases from the past 14 days that are in the current library. You can mark either feed as read independently. When the sidebar is hidden, use **我的关注** in the top bar.

See the [Chinese README](README.md) for build and usage instructions. The project is [MIT licensed](LICENSE) and is not affiliated with DLsite.

The desktop app also offers a separate all-age mode with its own database, preferences and favorites, plus a configurable recent-release collector with a release date range, minimum cumulative sales, new-release grace period and optional result limit.

An optional external library can mark works as collected, excluded, or both. In the desktop app, open **个性化** (Personalization), enter the lookup URL under **外部作品库接口**, and save it. Each profile keeps its settings and last results locally. It syncs at startup, supports manual refresh and independent hide filters, and keeps the last marks with a warning if the service is offline. See the [JSON lookup protocol](README.md#可选的外部作品库) to connect a compatible service.
