![Games](dist/assets/collection-banner.svg)

# GAMES

## A home for every great discovery.

[Real-time strategy](https://github.com/Herbertofury/Games/wiki/Real-Time-Strategy) | [RTS media atlas](https://github.com/Herbertofury/Games/wiki/RTS-Media) | [Boomer shooters](https://github.com/Herbertofury/Games/wiki/Boomer-Shooters) | [Roguelites](https://github.com/Herbertofury/Games/wiki/Roguelites) | [Download the interactive library](https://github.com/Herbertofury/Games/releases/latest)

A local-first collection built around actual recommendations, exact game identities, and source-grounded media. The current source contains 448 unique games: 170 roguelite entries, 150 shooter entries with two cross-genre overlaps, and 130 RTS entries. A store appearing twice does not create another game.

The RTS command center focuses on Command & Conquer: Generals - Zero Hour: base building, asymmetric factions, combined arms, AI skirmish, and major community overhauls. Conventional RTS, tactical-only games, fleet command, survival defense, prototypes, and upcoming projects remain distinct. Classic original release years are shown separately from later storefront editions.

## The collection experience

Genre-specific cinematic spotlights, full card/table/gallery views, structured search, filters, sortable Steam and native-platform ratings, explicit editorial recommendation, source-linked trailers and galleries, saved games, notes, personal ratings, play status, comparisons, saved views, CSV/JSON export, backup/import, deep links, dark/light themes, compact mode, keyboard support, and mobile layouts. Every record remains in the searchable dataset and DOM; there is no viewport virtualization.

Steam reception, recommendation fit, and personal rating are separate. A high thematic fit is not a claim of hands-on play-testing. Small review samples and weak reception constrain recommendations. Upcoming games have no current purchase-recommendation score.

## Canonical sources

- `data/seeds.tsv`: original roguelite identities.
- `data/shooters-*.json`: shooter discovery, creator projects, and editorial curation.
- `data/rts-seeds.json` and `data/rts-expansion.json`: RTS discovery and exact-edition reconciliation.
- `data/rts-steam.json`, `data/rts-external.json`, and `data/rts-storefronts.json`: official provider snapshots and checked alternate destinations.
- `data/rts-curation.json`: why a game belongs, base-building/skirmish distinctions, cautions, and original release years.
- `data/rts-media-completion.json`: audited media/edition corrections. Never substitute a different game, remake, or generic franchise image.
- `data/catalog.json`: the assembled canonical snapshot used by both app and wiki.
- `site/`, `scripts/`, `tests/`: application, build/update logic, and acceptance tests.
- `wiki/`, `dist/`, `release/`: generated wiki, portable website, and reproducible source/release ZIP.

[Update guide](docs/UPDATING.md) | [Execution and verification record](docs/EXECUTION.md)

## Rebuild the current snapshot

```sh
python3 -m pip install -r requirements-dev.txt
python3 scripts/build.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m http.server 8000 --directory dist
```

To explicitly refresh RTS providers before rebuilding, run `python3 scripts/enrich_rts.py --force`. Normal incremental refreshes reuse fresh snapshots. No hidden scheduled collector is installed. Generated wiki pages are pushed to the actual wiki only by the publishing workflow after its tests pass.

Personal data stays in your browser under the existing `games.library.v1` identity. Export a personal backup to move it between browsers/devices. Uncached images and videos require internet access. GitHub Pages is a separate deployment prerequisite; the native wiki and portable HTML do not require Pages to be enabled.
