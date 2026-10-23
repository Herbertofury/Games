# Add and update games

## Everyday browsing

Open the interactive library. Search names, developers, notes, tags or mechanics. Combine collection, Steam rating, review count, recommendation, release year, availability, play status, co-op and free filters. Save any combination as a named view. Card, table and gallery modes share the same result set. Every record stays searchable; there is no viewport culling.

Open a game for official trailers, all screenshots, your notes, your rating and play status. Compare two to four games. Share a filtered view or deep-link to a specific game. Export current results to CSV or JSON. Export your personal backup from Library settings before switching browsers or devices.

## Add a recommendation

Use **Add a game** in the library or the repository's Game recommendation issue form. Supply the official Steam URL or app ID, collection, and editorial fit. Owner-authored submissions can be imported by the add-game workflow; public submissions require owner review. There is no hidden scheduled collector.

For a direct edit, update `data/seeds.tsv`. One row per unique Steam app ID:

```tsv
appid	name	collection	fit
2218750	Halls of Torment	Dark fantasy	10
```

Preserve existing IDs and collections. Use a new collection label when appropriate. The refresh verifies the app ID against the title. Unverified games retain a visible pending record rather than fabricated facts.

## Refresh facts and republish

Open **Actions > Refresh Steam catalog > Run workflow**. It fetches the official metadata and reviews, rebuilds the website and wiki, runs checks, commits the new snapshot and publishes the outputs. Changes to the seed file also trigger refresh. This is a manual/update-driven pipeline, not an unrequested recurring schedule.

The browser's **Check for newer snapshot** button downloads the latest already-published snapshot. It does not secretly trigger GitHub Actions or fetch every Steam page from your browser.

## Local development

Requires Python 3.11+ and Node.js for syntax checks. The website itself requires no build framework and no npm dependencies.

```sh
python3 scripts/refresh.py --force
python3 scripts/build.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m http.server 8000 --directory dist
```

For browser QA:

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 tests/browser_qa.py
```

`release/Games - Explorer.html` opens directly in a browser. `release/Games - Library.zip` includes reproducible source, snapshot, wiki, website, and tests. `release/SHA256SUMS.txt` records release sizes and hashes.

## Publishing prerequisites

GitHub Pages must be enabled once in repository **Settings > Pages > Source: GitHub Actions**. The native GitHub wiki needs an initial page created through GitHub before its separate Git repository can be cloned. The publish workflow reports any unmet prerequisite; a repository-side wiki folder is never claimed to be a live wiki.

The generated wiki owns Home, Roguelites, Collections, Ratings-and-Sources, Updating-the-Library, Needs-Verification, the sidebar/footer, and its Game-* pages. Other existing wiki pages are preserved. New genre pages can be integrated without deleting unrelated content.

## Implementation notes

The canonical seed list owns the selection and editorial fit; the verified catalog owns factual metadata. A deterministic build produces the portable web app and wiki from the same data. No credentials or personal data are embedded in releases. Favorites and notes are local to a browser, not falsely advertised as cross-device synchronization. Full-dataset search and all record DOM nodes remain available; only image bytes are loaded lazily.

If an official stream fails, the detail page offers alternate trailers and a direct Steam fallback. HLS.js is loaded only for HLS playback. Offline mode retains the entire data/search experience but cannot manufacture uncached media.
