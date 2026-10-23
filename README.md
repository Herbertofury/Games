![Games](dist/assets/collection-banner.svg)

# GAMES

### A home for every great discovery.

[**Open the interactive library**](https://herbertofury.github.io/Games/) · [**Roguelite wiki**](https://github.com/Herbertofury/Games/wiki/Roguelites) · [**Download portable library**](https://github.com/Herbertofury/Games/releases/latest) · [**Add a game**](https://github.com/Herbertofury/Games/issues/new?template=game.yml)

A local-first, living game collection. Starts with every recommendation from the two roguelite discovery lists, plus Vampire Survivors as the reference game. Official Steam verification replaces unsupported prior claims; unresolved discoveries are preserved and clearly labeled.

## The collection experience

Cinematic spotlight, curated discovery lanes, card/table/gallery views, instant full-dataset search, structured search operators, faceted filters, multiple sorting modes, official embedded trailers, full screenshot galleries, Steam links, saved games, personal notes and ratings, play status, recent history, saved views, four-way comparison, CSV/JSON exports, backup/import, shareable links, dark/light themes, compact mode, keyboard controls, responsive mobile layout, and graceful offline operation.

**Steam reception, editorial recommendation, and your own rating are separate.** Recommendation is fit for the requested style, not a claim of play-testing. Review sample size and snapshot age stay visible.

## Canonical data and updates

- `data/seeds.tsv`: unique Steam IDs, selection, collection, editorial fit.
- `data/catalog.json`: official verified metadata, review totals, screenshots, trailers, timestamps and source URLs.
- `site/`: application source; no runtime framework or required npm build.
- `scripts/`: refresh, build, add-game and publication tools.
- `wiki/`: generated pages mirrored to the actual wiki when its repository exists.
- `dist/`: published web app, snapshot, and provenance manifest.
- `release/`: portable HTML, full source/release ZIP, and SHA-256 sums.

[Update guide and implementation notes](docs/UPDATING.md) · [Execution and verification record](docs/EXECUTION.md)

## Rebuild

```sh
python3 scripts/refresh.py --force
python3 scripts/build.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m http.server 8000 --directory dist
```

Personal browser data is not sent to GitHub or Steam. Export a personal backup to transfer notes/favorites between devices. Remote artwork and trailers require internet access. Initial Pages/wiki enablement, when needed, is reported rather than hidden.
