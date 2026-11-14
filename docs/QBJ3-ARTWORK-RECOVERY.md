# QBJ3 card artwork recovery, 2026-11-14

Games publication run 43565983989 at source af5eafd2 failed its complete
shooter image decode gate. Artifact 14103251181 (`qa/source-completion-qa.json`)
identified exactly one failed card, `external:qbj3`. The previous logo URL
`https://media.moddb.com/images/mods/1/71/70326/qbj3logo_1024x768.png` independently
returned HTTP 404. The gate was retained unchanged.

The canonical external-source layer now uses the existing QBJ3 gallery image
`https://media.moddb.com/images/mods/1/71/70326/qbj3_hcm.jpg` for the card and
trailer poster. This is the same project, not a substitute game or generated art.
The creator's [ModDB project page](https://www.moddb.com/mods/quake-brutalist-jam-iii)
continues to publish the qbj3_hcm image. All five existing gallery links returned
HTTP 200. No images were copied into the repository or relicensed.

A fresh replacement response decoded as JPEG, 1920x1080, 244744 bytes, SHA256
`bc42a7969524baec919f2b048c04153d5cb6a88af15aa262ac7a1163d6d2a477`.
This is the observed response, not a promise that the CDN never changes bytes.
Browser decode and the complete publication gates must pass before claiming
Wiki/Pages/release delivery. Stable game ID, gallery, stores and trailer ID
remain unchanged. The previous failure remains in the original CI artifact.

Rebuild comparison: all 1853 stable IDs retained; exactly one record changed,
QBJ3, and only its `image` and trailer poster. Dataset hash changes from
`b2571a5892d17b23994477080f616e64d9177ae78344e99bdfe9407b87063cbb`
to `21cd8d7e36c0adfa808b645b7a491530be54e9820c918c34a93cfa612cb293a0`.
The lounge exact-catalog regression pin is advanced to this verified correction,
not removed or relaxed. A PR gate now runs the same complete shooter browser
acceptance before source corrections merge; it does not bypass publication QA.
