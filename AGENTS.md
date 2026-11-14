# Repository instructions

Read `.agents/foundry/AGENTS-adapter.md` for the pinned shared engineering core.
Keep this file and nested instructions project-owned: setup, commands, constraints and acceptance belong here.

## Games-specific engineering contract

Read `README.md` and `docs/UPDATING.md`; for catalog, media or library state work, use `.agents/skills/catalog-acceptance/SKILL.md`.

- Preserve stable game IDs and the browser's `games.library.v1` identity. Store links are not separate games; distinguish original, remake, DLC, demo and soundtrack editions.
- Keep source reception, editorial fit and personal rating separate. Unknown media, unavailable providers and untested playback must remain explicit; preserve last-good snapshots when refresh fails.
- All records remain searchable and in the DOM; do not introduce viewport virtualization as an unrequested optimization.
- Local baseline: `python3 scripts/build.py` and `python3 -m unittest discover -s tests -p 'test_*.py'`. Browser acceptance uses actual generated `dist`, not source-only syntax. Read each script before use; collectors contact providers and publication workflows update wiki/releases/Pages.
- Preserve optional Steam sync and account boundaries. Do not require a connected account for the local-first library, or publish private browser state/account data with public catalog evidence.
