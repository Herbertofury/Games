# Games: the Metroidvania exploration atlas

This release adds a dedicated hub with 430 source-grounded Metroidvania and explicitly labelled adjacent entries to the same living library. The complete library now contains 1189 unique records. Every previous genre identity and the existing browser-storage key remain intact.

Every published Metroidvania entry has real artwork, an exact embedded-video source, and confirmed distribution links. Creator trailers, credited community gameplay, historical alpha footage, creator animated gameplay loops, and a catalog-recorded public Spellsought preview are labelled distinctly. Two candidate previews that could not be verified remain in the research ledger, not among recommendations.

Separate shelves cover traditional Metroidvanias, dark fantasy, parry-focused combat, alien worlds, movement challenges, puzzle-led labyrinths, miniature freeware, top-down/3D neighbors and roguelite hybrids. Recent releases, demos, prototypes, console editions and upcoming games are clearly distinguished. Original Castlevania titles are searchable inside their official collections.

Native wiki: Metroidvanias, Metroidvania-Media and Metroidvania-Underground, plus individual game dossiers. The wiki renders artwork and links videos; the portable HTML supplies the embedded players.

Source coverage is the confirmed set, not a claim to every retailer worldwide. Patreon support is not a full-game license; Nintendo Classics membership access is not freeware. Review scores retain their provider and sample size. Editorial fit is not a claim of hands-on completion.

The release gate retains all previous browser and unit tests and adds exhaustive new detail/source and artwork checks. Actual video-playback probes are distinct from a claim that every external video was watched end to end. GitHub Pages remains a separate hosting setting.

## Snapshot counts

```json
{
  "records": 430,
  "statuses": {
    "Released": 382,
    "Early Access": 9,
    "Upcoming": 36,
    "Prototype": 3
  },
  "sourceReferences": 723,
  "providers": {
    "Steam": 522,
    "GOG": 108,
    "itch.io": 70,
    "Official site": 5,
    "IndieDB": 2,
    "PlayStation": 1,
    "Konami": 1,
    "Humble Store": 5,
    "Nintendo": 7,
    "Patreon": 2
  },
  "datasetHash": "b976cf3e15d542b777e30da58c984b7169c3ca90220152ec6808c7fc7bab9512"
}
```

## Updating

Use Refresh Metroidvania discoveries or run `python3 scripts/enrich_metroidvania.py`, then `python3 scripts/build.py`. Stable IDs and previously resolved candidates survive discovery-index changes. Creator caches expire after one day; store caches after seven days. `--force` invalidates them explicitly. Curation, corrected media, reviewed candidates and captured-preview provenance remain separate source layers. No scheduled crawler is enabled.
