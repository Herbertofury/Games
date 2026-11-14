---
name: catalog-acceptance
description: Update and validate the Games catalog, exact-edition media, stable personal data and generated library/wiki without mistaking fixtures or provider metadata for playback proof.
---

# Games catalog acceptance

Use for discovery ingestion, source refresh, media corrections, generated library changes and personal-state migrations. Read `README.md`, `docs/UPDATING.md` and the affected genre's source files first.

## Change the right layer

1. Record the starting commit and relevant source snapshots. Follow the README's canonical inputs; edit seed/editorial/provider layers rather than patching generated `dist` or `data/catalog.json` alone.
2. Reconcile exact identity before accepting a candidate: Steam AppID or stable external project key, edition, release state and requirements. A store redirect, matching name or franchise image is not evidence of identity. Preserve IDs across title changes and alternate stores.
3. Attach source URLs and checked dates to factual corrections. Keep proposed discoveries unresolved until verified. No fabricated review scores, release dates, purchase recommendations or hands-on claims.
4. Preserve last-good data on provider failure. Report blocked/auth-required/missing media separately from empty collections. Never export account tokens or private Steam/browser state to catalog fixtures.

## Rebuild and inspect

Use an isolated checkout. Install `requirements-dev.txt` in an isolated Python environment if needed. Run `python3 scripts/build.py` then `python3 -m unittest discover -s tests -p 'test_*.py'`. Inspect generated diffs for removed identities, unintended source replacement and unrelated changes. Keep a before/after count by stable ID and explain every removal or merge.

For affected interactive behavior, inspect and run the relevant actual browser harness against built `dist`, for example `tests/browser_qa.py`, `tests/multiplatform_qa.py` or `tests/source_completion_qa.py`. Chromium availability is a prerequisite, not an assumed pass. Source/media collectors and `--force` are explicit network-refresh steps, not mandatory parts of a documentation-only change.

## Acceptance matrix

- One record per stable ID, alternate stores attached to the right edition; original and later storefront release dates not conflated.
- Full catalog remains in the searchable dataset and DOM across grid/table/gallery, filters, sort and genre changes; no hidden loss through virtualization.
- Recommendations, Steam/native reception and personal ratings remain independent. Unreleased/unknown entries have honest states.
- Favorites, notes, status, rating and saved views survive reload; exported backup imports without silent loss under `games.library.v1`. Test interrupted/repeated import and retain a backup before any migration.
- Check media identity, image decode and gallery navigation. Label metadata-only, player-ready and actually-playing evidence separately; test play/close/navigation without unintended autoplay or continuing audio.
- Exercise keyboard dismissal, mobile layout, reduced motion, empty/error states and optional Steam service absence. Core local library must remain useful without account access.

Record commands, exact build identity, failures and evidence paths. Generated wiki files are not proof of live wiki publication; remote release, Pages and native wiki need separate verification only when publication is authorized. Do not dispatch publishing or collection workflows merely to test this skill.
