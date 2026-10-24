# Games Lounge 2.0

A Steam-inspired, animated library and a delightfully silly original desktop arcade. The same 1853 canonical entries, source links, trailers, player counts and genre memberships are preserved.

Cinematic spotlights, living background, hover screenshot previews, personal capsule shelves, complete sidebar title browser, history controls, right-click menus, game-detail section navigation, Big Picture, full screen and a filter-aware wildcard picker. All original library filters, table/card/gallery views, comparisons, notes, ratings, favorites and exports remain available.

Snackball is an actual local Canvas game: move, collect stars, throw a returning donut, bonk bots, play a 60-active-second round and save a best score. Includes a draggable/resizable desktop window, touch controls, pause/resume, and optional silly physics. The passive scene never intercepts library clicks.

Three atmosphere palettes, system/full/reduced/off motion, focus mode, independent background/hover/spotlight controls, and optional quiet sound effects. Sound starts off. Scene loops stop for hidden tabs or dialogs, and the game pauses on focus loss. No new runtime dependency, account integration, scheduled scraper or generated replacement artwork.

The complete catalog remains in the DOM, not virtualized. Cached number formatting removes repeated formatter construction with identical output. Existing personal game storage is unchanged; lounge preferences and arcade best score use separate namespaced device-local keys.

Open the portable HTML in a browser. The native wiki describes the lounge and preserves all game pages, while animation and the arcade live in the HTML. GitHub Pages remains a separate hosting prerequisite. Verification artifacts report the tests that actually completed; this release description is not itself a test result.

## References and implementation decisions

Steam library interaction reference: https://store.steampowered.com/libraryupdate
Browser-native motion: https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API
Time-based rendering: https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame
PixiJS was evaluated against this small original Canvas scene: https://pixijs.com/8.x/guides/components/application . Native Canvas was selected because it preserves the portable zero-dependency build without a rendering-engine bundle, GPU-only requirement or CDN. No upstream code was copied.

The existing verified data model and source-media player are reused unchanged. Only the presentation and original game layer are new. Local managed Chromium blocks navigations; inline local smoke tests do not claim persistence or network proof. Full production navigation, persistence, image decoding and video acceptance run on the established GitHub Actions Chrome route.
