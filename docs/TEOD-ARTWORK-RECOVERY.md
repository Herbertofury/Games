# The End of Days artwork recovery

The full publication run [43568792571](https://github.com/Herbertofury/Games/actions/runs/43568792571) on `327382e4` passed the repaired shooter gate, then failed the RTS all-artwork decode gate. Retained artifact `14103527517`, `qa/rts-qa.json`, identifies exactly `external:end-of-days-zh` and the old `TEOD_logo.png` URL. A direct read independently returned HTTP 404 on November 14, 2026. Wiki, release and Pages publication were skipped, not successful.

Use the already-attributed GLA Fortress gallery image from the same ModDB project and directory. Its retained thumbnail decodes at 120x90; the original-resolution JPEG decodes at 1919x1079 (1,186,261 bytes; observed SHA256 `70fd9278d89905f5717d7ffb1b2b9a32e4600f3bb895cfb22690163c319c9c5f`). This is a response observation, not an immutable CDN promise. The main creator page returned 403 to the research fetch; no access restriction was bypassed. Provenance is the existing catalog's attributed gallery, corroborated by the accessible matching original and thumbnail, not a newly claimed page review.

- Project: https://www.moddb.com/mods/the-end-of-days
- Original artwork: https://media.moddb.com/images/mods/1/12/11840/GLA_-_Fortress.jpg
- Existing thumbnail: https://media.moddb.com/cache/images/mods/1/12/11840/crop_120x90/GLA_-_Fortress.jpg

Preserve the exact Zero Hour mod identity, requirements, gallery, distributions and all 1,853 stable IDs. Only its primary image and first gallery original resolution change. The source fixture checks identity and build retention; the PR workflow runs the existing full RTS browser harness without relaxing its network/decode or playback requirements. A passing PR does not prove full publication: verify the subsequent main run, native wiki, downloadable release and served site separately.
