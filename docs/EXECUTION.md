# Games execution and acceptance record

## Canonical identity

Repository: https://github.com/Herbertofury/Games
Native wiki: https://github.com/Herbertofury/Games/wiki
Target interactive home: https://herbertofury.github.io/Games/
Original main: c69d8b00d845ee01fd0b836dee717bcf4f85e235
Initial source checkpoint: 590c697f8380a4f4f0c300e40c22abb17bd24e93
Initial official metadata run: 39894224458, job 120220781043

## Scope

Preserve every prior recommendation, deduplicate IDs, verify official Steam facts, distinguish pending records, and provide a beautiful permanent home. Filters cover ratings, genres/mechanics, release dates, editorial recommendation, availability, personal status, co-op, free games, and media. Direct official media and Steam links, complete galleries, personal organization, comparison, exports, accessibility, mobile behavior, transparent updates, and native wiki publication are acceptance items.

## Implemented

The canonical seed list and official Steam refresh workflow are committed. A dependency-free local-first app, deterministic wiki/site builder, issue-based owner-reviewed additions, generated release manifest, portable archive, publication scripts, and unit/browser test suite are implemented. No scheduled collector, image generation, credentials, or analytics is used. No recommendation records are culled from the DOM for performance.

## Verification and environmental boundaries

The local sandbox cannot reach external hosts and its managed Chromium blocks navigations. Inline offline Chromium testing is a separate smoke lane; it does not claim real storage persistence or live media proof. Full navigational QA executes on GitHub Actions against the actual verified snapshot, with desktop/mobile/detail screenshots and JSON evidence.

A remote generated snapshot, live wiki push, Pages deployment, and release upload are distinct outcomes. The publishing report records them separately. Unmet first-page/wiki or Pages settings remain unresolved rather than being labeled complete. Do not repeatedly retry unchanged provider or browser-connection failures.

## Update and continuity

Keep the same repository, seed IDs, snapshot, and generated-page ownership. Rebuild from changed canonical facts. Preserve unrelated wiki pages and user browser data. Check `docs/qa` and the exact most recent workflow run before continuing; do not restart source discovery. Resume from the first unresolved publication or test item, then verify remote lineage and release hashes.
