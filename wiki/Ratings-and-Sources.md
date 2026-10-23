# Ratings, recommendations, and sources

## Three distinct scores

**Steam rating** is the positive percentage across all languages and all purchase types, with the full review count beside it. This can differ from the localized Steam store headline. Small samples are flagged.

**Recommendation** is editorial relevance to the requested style, on a 1 to 10 scale. It is not a claim of hands-on testing. Start here: 9 to 10. Strong picks: 8. Explore: 7. Deep cuts: 6 or below. A verified game's initial fit is set in the seed file. Fewer than 30 reviews cap the score at 7. With at least 30 reviews, under 50% positive caps it at 5, under 70% at 6, and under 80% at 7. Unverified identities receive no score. Upcoming games are watchlist entries.

**Your personal rating** is your own score after playing, stored privately in your browser alongside notes and play status. It never overwrites Steam reception or the editorial recommendation.

## Provenance

The two earlier recommendation lists are discovery inputs, not evidence. Current identity, availability, date, price, developers, screenshots and trailers are fetched from Steam's store API. Review totals come from Steam's review API. Every verified entry carries its source URLs and timestamp. Ambiguous identity matches are held for verification. No invented dates, scores, screenshots, or trailer IDs are inserted.

Steam's store release date can reflect full release rather than the first Early Access launch. Prices are US-store snapshots and must be rechecked before purchase. A removed or inaccessible listing is not silently deleted. Refresh failures retain the previous verified snapshot, original verification timestamp, and a warning.

## Media and offline use

Official developer artwork and trailers are served by Steam. Native MP4/WebM video is preferred; HLS.js 1.7.3 handles official HLS streams in compatible browsers. A blocked or absent stream retains an obvious Steam fallback. Screenshots have full-image viewing, thumbnails, and keyboard navigation.

The standalone HTML keeps the entire searchable catalog offline. Remote images, fonts and video require a connection unless already cached. No account, API key, analytics, or advertising is required.

## One source of truth

`data/seeds.tsv` owns the selection, collection and initial editorial fit. `data/catalog.json` owns the verified snapshot. The website and wiki are generated together. Personal browser data is independent; export a backup to transfer it between devices.
