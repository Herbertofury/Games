# Steam discovery for Athena design research

The existing Games application already filters/sorts reception and genre, supports media and keeps editorial and personal ratings separate. `scripts/export_design_catalog.py` exposes a read-only machine-consumable projection of that same catalog rather than creating another disconnected library. It needs no Steam login and never touches personal preferences.

```sh
python scripts/export_design_catalog.py --label 'Overwhelmingly Positive' --genre Action --feature Single-player --min-reviews 100 --sort rating --output /tmp/athena-game-design.json
python scripts/export_design_catalog.py --label 'Mostly Positive' --sort reviews
python scripts/export_design_catalog.py --label unknown
```

Labels are actual retained Steam labels, not inferred from percentages. Genre and feature are exact case-insensitive facets. Filters combine; all matching records are exported with no hidden sample limit. Unknown ratings sort after known values, including zero. Sample counts and source times remain attached. Output preserves artwork, galleries and trailer metadata, not proof of playback or a license to redistribute assets. One stable Steam AppID remains one record.

## Evidence rather than praise hallucination

An aggregate review rating cannot explain *why* players like a game. `editorial` is explicitly curator interpretation, never player consensus. Optional `--studies PATH` joins `Modding-Knowledge/data/game-progression-evidence.json` by exact ID and emits observations, source URL/date, interpretation, acceptance questions and playtest state separately. Missing evidence stays null. Example:

```sh
python scripts/export_design_catalog.py --studies /path/to/Modding-Knowledge/data/game-progression-evidence.json --sort rating --output /tmp/athena-evidence.json
```

This supports downstream inspiration briefs without pretending source metadata establishes novelty, successful implementation or popularity of an individual feature. Review-text analysis, representative review sampling and user-study evidence are future work; no review corpus was collected in this change.

## Freshness and scope

The export includes the exact source-catalog SHA256 and catalog-generation date. Each review retains its original observation timestamp, refresh error and matched review API request parameters (including languages, purchase type, filter and day range). Unknown/missing parameters are not guessed. Source URLs for another AppID are excluded from scope evidence. A fixed 30-day freshness window is a display policy, not a guarantee of accuracy. Missing or timezone-less timestamps remain unknown; future-dated evidence is explicitly flagged. Stale last-good records remain visible.

The canonical snapshot covers a curated collection, **not all Steam games**. It is not refreshed by export and has no new scheduler. Future continuous mining should use existing collectors, retain last-good results, document failures, keep release states separate, and compare changed evidence. Do not treat a snapshot's `generatedAt` as the observation time of every game. Steam and other-platform rating scales must not be merged.

## Verification and limits

Tests cover real-catalog record preservation, combined label/genre/feature/sample filters, numeric sorting, unknown-last, freshness, duplicate/mismatched identity, exact review-request provenance and optional exact-ID evidence joins. This is a CLI consumer contract, not an integrated Athena UI, browser playback test, automatic Steam-wide crawler or subjective-best ranking. Existing Games UI and personal storage are unchanged. Next work: consume the export in Athena's visual research library, link research to per-project ideation and validate native filters before claiming that complete user flow.
