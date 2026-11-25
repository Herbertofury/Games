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

## Mandatory CLI-first / non-interruptive execution

For every task, follow the owner-mandated [Athena CLI-first execution standard](https://github.com/Herbertofury/Athena/blob/main/guidance/CLI_FIRST_EXECUTION.md). Prefer fast official CLI/headless commands, supported APIs/SDKs/connectors and tested local automation. If a required application has no usable structured interface, discover or build a reviewed [CLI-Anything](https://github.com/HKUDS/CLI-Anything) harness over the real supported backend (or a native command surface for first-party code). Use isolated browser/renderer/test sessions for necessary UI proof. Never take over the user's active desktop, mouse, keyboard, focus or browser profile without explicit authorization for unavoidable foreground interaction. Preserve real runtime acceptance, data, permissions, feature parity and portable mode. Record reusable command coverage and unresolved gaps; no fake CLI parity or unnecessary release delay.

## Game Systems Exchange and release radar

This repository is the source-backed discovery/research input for [Athena's Game Systems Exchange](https://github.com/Herbertofury/Athena/blob/main/docs/GAME-SYSTEMS-EXCHANGE.md) and [coordination issue #364](https://github.com/Herbertofury/Athena/issues/364). Keep roguelike, roguelite, deckbuilder and card-game records distinct; preserve official release status, developer/source links, dates, platform/runtime, licensing and evidence. A researched game or marketing description is not hands-on gameplay verification and is not a reusable engine implementation.

When an exceptional mechanic or major release is identified, add its official source and precise mechanic to the appropriate catalog record, then route the evidence to Athena's gameplay capability registry. Prefer concrete adopt/adapt/research/skip recommendations and note which app/mode could benefit. Do not copy proprietary game code, art, card text or assets; respect license and attribution. Routine patches do not need a notification.

## Athena Engine Foundry — shared game-engine source of truth

Before creating or materially changing card-game rules, deckbuilding, roguelite runs, survivor combat, encounter/reward systems, mascot actors, open-world simulation, vehicles, missions, save progression or game runtime/rendering, consult [Athena Engine Foundry](https://github.com/Herbertofury/Athena/blob/main/docs/ENGINE-FOUNDRY.md), its [package catalog](https://github.com/Herbertofury/Athena/blob/main/engines/catalog.json), and [M5 issue #365](https://github.com/Herbertofury/Athena/issues/365). Reuse or improve the strongest verified compatible engine; contribute generic improvements and fixtures back to Athena. Keep this repository's unique content, UI, balance, assets, saves and host adapters local. Do not create a parallel engine or independently edit an immutable Athena intake snapshot. Consumers must pin an exact local package/source digest, pass their own full acceptance and retain rollback; no application runtime may depend on an online Athena service. A source candidate or prototype is not a verified engine release.
