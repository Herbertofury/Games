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

## Mandatory pre-release optimization gate

Before finalizing every release, follow the owner-mandated [Athena zero-loss pre-release optimization standard](https://github.com/Herbertofury/Athena/blob/main/guidance/PRE_RELEASE_OPTIMIZATION.md). Evaluate shrink-anything, fast-anything and rust-anything using reviewed pinned tools in isolated worktrees; run applicable passes, compare equivalent complete workloads, keep only independently verified improvements, restore rejected changes, and record per-tool evidence or explicit inapplicability/blockers. Never weaken tests, delete required content, force a Rust rewrite or regress functionality, quality, portability, compatibility, security or protected performance metrics. Data/documentation-only releases and existing native Rust paths require honest applicability decisions, not artificial ports. Existing local and pinned governance requirements remain intact.
