# Platformer completion: source media and primary routes

This follow-through completes the already published 439-record platformer study rather than replacing the library or starting a disconnected catalogue. The comparative study, ten routes, 121 individual editorial notes and broader source-grounded discovery remain in `PLATFORMERS-STUDY.md` and the native Wiki.

## What changed

The previous snapshot explicitly reported twenty entries without a playable video source. `data/platformers-media-reviewed.json` now provides an additive, independently reviewed media record for those identities. It cannot replace game IDs, release dates, ratings, artwork or edition facts. Normal Steam refreshes therefore cannot erase these manual source corrections.

Ten Nintendo videos come from the exact product slug's own gallery metadata, not recommendation carousels. Two older Nintendo videos are the streams actually requested by the featured Play Nintendo players. Publisher uploads are checked against exact video titles and uploader identities. Celeste 64 uses clearly credited GIGAZINE gameplay rather than being misrepresented as a developer trailer.

CELESTE Classic and Celeste Classic 2 use short recordings of the exact public browser builds linked by their creators. These are labelled **Library-captured public browser preview**, credited accordingly and marked `official: false`. They are not commercial Celeste, generated footage, full playthroughs or comprehensive playtests. An earlier title-screen-only capture was rejected. Approved recordings show actual character movement and were visually checked using start/motion/end screenshots and independently extracted frames at 10, 14, 18 and 22 seconds.

The approved capture bytes, source artifact and source metadata are bound to SHA-256 hashes in `data/platformers-preview-approval.json`. Their playback URLs pin the exact asset commit rather than a mutable branch. The importer reads only the approved JSON and two named WebM files; it does not execute downloaded artifact content or extract a source archive over the repository.

## Navigation correction

The platformer sidebar and collection counter now use each game's single primary platformer route. Shared shooter and Metroidvania memberships remain on the canonical records, but no longer inflate the platformer navigation beyond its ten study routes. Card labels use a view-specific copy; the underlying shared identity and other hubs are unchanged.

## Verification contract

`tests/test_platformer_completion.py` verifies all 439 platformer entries have artwork and supported video metadata, all twenty additions have appropriate provenance, media overlays cannot alter game facts, capture files match approved hashes, pinned URLs are immutable, Nintendo product identities match, and the historical Shovel of Hope DX announcement does not turn the current watchlist entry into a released-game recommendation.

`tests/platformer_completion_qa.py` runs the production application in Chrome. It plays all fourteen newly added direct streams and recordings until decoded frames and time advancement are observed. It separately checks the six YouTube videos' live title/uploader metadata, consent-first loading and exact privacy-enhanced embed URLs. The latter is not an assertion of end-to-end YouTube playback. It also checks all ten sidebar counts, all hub memberships, returning between hubs, and desktop/mobile layout.

These checks supplement all existing unit tests, the complete platformer-detail and artwork gate, and the original library, shooter, RTS and Metroidvania browser suites. No installed collection's acceptance tests are disabled. The final tested HTML hash must match the rebuilt release before generated outputs are committed.

## Reading the evidence

The source and source-recovery reports describe metadata and capture approval. `docs/qa/platformers-completion-qa.json` describes actual runtime checks after they pass. `data/platformers-study-report.json` provides current coverage counts. Native Wiki, downloadable-release and Pages publication have separate receipts. A successful build is not itself proof that a website deployed; GitHub Pages still requires its repository hosting prerequisite.

The scope remains a broad curated study, not an exhaustive inventory of every platformer ever released. Original launches, later storefront editions, playable demos, announced projects and hardware requirements retain their distinctions. Individual editorial notes are labelled separately from subgenre study lenses, and none of the study's rankings are presented as personal play-tested review scores.
