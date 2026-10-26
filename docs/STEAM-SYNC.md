# Steam integration: implementation and deployment boundaries

## Included

The Games interface can import Steam/GameSync JSON locally, match exact Steam AppIDs, distinguish owned/wishlisted/tracked records, filter and sort by known playtime or wishlist priority, export a credential-free snapshot, and clear Steam data without clearing notes/favorites. Private or unavailable lists are not silently treated as empty. A failed refresh keeps the dated last-good list for the same identified account.

GameSync-Next was inspected as the user's design reference. This is an independently written adapter for its game-record shapes, not publication of the private repository. Importing a tracked GameSync record does not establish a Steam license; only explicit ownership or an explicit self-report option marks it as owned.

## Wishlist actions

`Wishlist on Steam` and `Manage wishlist on Steam` open the exact official app page. The user completes the addition or removal there and refreshes the local snapshot. `Open in Steam` uses the installed Steam client. This release does NOT claim one-click remote wishlist mutation.

The earlier, uncommitted cookie/session-based extension draft is excluded. No Steam cookies, passwords, Steam Guard codes, or undocumented wishlist-write requests are handled by this release. OpenID verifies identity; it does not grant wishlist editing permissions. True in-site wishlist writes need a separately reviewed, explicitly authorized integration and live verification before they can be claimed as supported.

## Online sign-in and sync

`services/steam-sync/server.mjs` is a separate read-only Node 22 service. GitHub Pages cannot execute this server. `site/steam-config.json` intentionally has an empty `serviceUrl`; sign-in stays visibly disabled until the operator deploys a verified HTTPS service.

The service validates Steam OpenID assertions with Steam, checks return URLs, signed fields and nonce freshness, binds the callback to the initiating browser, and exchanges a one-use code with a verifier for a short-lived memory-only session. Frontend sessions are not written to localStorage. Steam API keys remain in the server's environment. The session can sync only its verified SteamID, not an arbitrary ID supplied in a request.

Owned games use `IPlayerService/GetOwnedGames` with a server-side user API key and visible game details. Wishlist reads use Steam's `IWishlistService/GetWishlist` response and fail conservatively if its shape or availability changes. Missing arrays are not silently interpreted as empty.

## Deployment

1. Deploy the repository's `render.yaml` Blueprint or run `node services/steam-sync/server.mjs` on an HTTPS-capable Node host. Creating a deployment is a separate operator action, not a consequence of committing this file.
2. Set `APP_URL=https://herbertofury.github.io/Games/` and a clean HTTPS `PUBLIC_BASE_URL` (Render's `RENDER_EXTERNAL_URL` is accepted). Set `STEAM_WEB_API_KEY` privately in the host's secret environment settings. Never commit the value or paste it into a visitor form.
3. Confirm `/health` identifies `games-steam-sync`, version 1, and the exact frontend origin. Then put only the HTTPS service origin in `site/steam-config.json` and run the existing publishing pipeline.
4. Perform a real Steam sign-in and test public/private/empty list cases with authorized test accounts. Automated fixtures are not proof of a live Steam login.

This initial backend stores sessions/nonces in process memory: use ONE service instance. A restart invalidates sessions. Multi-instance deployments require a shared atomic nonce/session store before enabling scaling. Rate limits are bounded but proxy-aware per-client limiting belongs at the host/edge; forwarded IP headers are deliberately not trusted implicitly. Configure host request logs to avoid authentication callback query strings. The response pages and API use no-store/no-referrer protections.

The frontend shares the GitHub Pages account's origin with other projects under that account. A dedicated custom domain is recommended for a stronger same-origin security boundary. Cloud synchronization of personal notes is not part of Steam sign-in.

## Verification

Run `node --test tests/steam-model.test.cjs services/steam-sync/server.test.mjs tests/steam-wishlist.test.mjs`, the existing Python source suite, and `python tests/steam_browser_qa.py`. Browser tests use real Chromium and this real backend with an explicitly mocked Steam upstream. They cover popup/callback/exchange, imported lists, privacy failures, exact links, notes preservation, disconnect and mobile layout. They do not mutate any user's real wishlist.

## Primary references

- Steam authentication/OpenID: https://partner.steamgames.com/doc/features/auth
- Steam owned-game visibility and GetOwnedGames: https://partner.steamgames.com/doc/webapi/IPlayerService
- GitHub Pages static-hosting boundary: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

Implementation status is distinct from deployment status: an empty service URL means live sign-in is NOT active.
