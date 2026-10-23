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

## Boomer shooter expansion, October 23, 2026

Acceptance: extend the same source repository, actual wiki, and portable app. Preserve the 170 original recommendations and browser storage. Add broad current shooter research including smaller hosts, creator support, explicit requirements, native ratings, media, and clear demo/prototype labels. Do not replace original lists or inflate game counts with alternate-store duplicates.

Original published main: `744baec1a6fa846d3818d06bc5854d4e93389a78`.
Discovery source commit: `2e01d1ed5de7581285b598e2447230db187c3c63`.
Initial Steam discovery run: `39911217448`; artifact `12482658594`; SHA-256 `d8606baa8d5d7f5c8c6b983ab3542432b74d555df5a90513a7fedfb29f156445`.
The initial pass resolved 121 of 126 candidates. Captain Wayne, Impaler Gold, and GTTOD were reconciled to explicit IDs; Shrine was moved to its official creator release; Fresh Supply was recorded as an archival edition rather than advertised as newly purchasable. DEAD TRASH and MALEDICTOR were added with explicit official IDs.

Implemented local checkpoint: provider-aware merged model; genre hubs; platform/build/style/native-rating filters; source and requirement panels; opt-in creator embeds; original saved-state compatibility; matching native wiki generation; incremental Steam and creator-media refresh; 16 passing unit tests and a passing inline genre smoke test. Real browser/network validation remains a distinct publication gate.

Known recovery: container outbound DNS and managed navigation are restricted. Use GitHub Actions for current provider metadata and real Chrome acceptance. The current hosted Chrome successfully plays Steam HLS; the older managed Playwright Chromium did not. Do not repeat older-codec experiments. Workflow files must be committed through the GitHub connector, not written by the workflow token. Preserve the tested HTML hash before the final documentation/package rebuild. Force-add only the intended `docs/qa` evidence because the generic `qa/` ignore matches it.

Exact next action at source checkpoint: run the incremental shooter and public-creator media collectors; build the merged snapshot; run full catalog, cross-platform, and live-media acceptance; publish and read back the native wiki and release. Record actual outcomes in `docs/qa`, not assumed success. No scheduled crawler or hidden watchdog was added.
