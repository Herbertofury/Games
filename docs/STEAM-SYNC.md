# Steam integration: implementation and deployment boundaries

## Included

The Games interface imports Steam/GameSync JSON locally, matches exact Steam AppIDs, distinguishes owned/wishlisted/tracked records, filters and sorts by known playtime or wishlist priority, exports a credential-free snapshot, and clears Steam data without clearing notes/favorites. Private or unavailable lists are not silently treated as empty. A failed refresh keeps the dated last-good list for the same identified account. Unidentified imports replace rather than guessing cross-account merges.

GameSync-Next was inspected as the user's design reference. This is an independently written adapter for its game-record shapes, not publication of the private repository. Importing a tracked GameSync record does not establish a Steam license; only explicit ownership or an explicit self-report option marks it as owned. Stable `steam:AppID` keys and Steam source IDs can fill missing `platformId` fields. Explicitly signed-out exports are rejected even when they contain cached IDs.

## Wishlist actions

`Wishlist on Steam` and `Manage wishlist on Steam` open the exact official app page. The user completes the addition or removal there and refreshes the local snapshot. `Open in Steam` uses the installed Steam client. A matched owned game also has `Launch in Steam` in its detail panel.

Game details offer **Valve's official store widget**, loaded only after explicit user activation. Valve documents an Add to Wishlist button for unreleased games and purchase controls for released games. Browser settings or Steam sign-in may require completing the action on Steam. The frame is cross-origin, sandboxed and no-referrer; Games does not read its account state or infer success from loading/clicking it. No automatic cart, purchase or wishlist action is sent by Games.

This release does NOT claim universal one-click wishlist mutation for released games. The earlier uncommitted cookie/session-based extension draft is excluded. No Steam cookies, passwords, Steam Guard codes, or undocumented wishlist-write requests are handled by this release. OpenID verifies identity; it does not grant wishlist editing permissions.

## Online sign-in and sync

`services/steam-sync/server.mjs` is a separate read-only Node 22 service. GitHub Pages cannot execute this server. `site/steam-config.json` contains only the deployed HTTPS service origin. An empty or invalid `serviceUrl` keeps sign-in disabled; deployment details and remaining real-account verification are recorded below.

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

Run `node --test tests/steam-*.test.* services/steam-sync/server.test.mjs`, the existing Python source suite, `python tests/steam_browser_qa.py`, and `python tests/steam_widget_qa.py`. Browser tests use real Chromium and this real backend with an explicitly mocked Steam upstream. They cover popup/callback/exchange, imported lists, privacy failures, exact links, notes preservation, disconnect, widget consent/identity, all genre counts, portable-file startup and mobile layout. They do not mutate any user's real wishlist.

The mock service replaces only the initial HTTP provider redirect with an equivalent new navigation because Playwright routes only the first URL of a redirect chain. This ensures the provider fixture intercepts the Steam URL instead of accidentally reaching the real Steam login page. Production retains its real HTTP redirect and full assertion verification. The widget fixture verifies placement and consent, not a real account action.

## Primary references

- Steam authentication/OpenID: https://partner.steamgames.com/doc/features/auth
- Steam owned-game visibility and GetOwnedGames: https://partner.steamgames.com/doc/webapi/IPlayerService
- Valve's store widget and upcoming-game wishlist button: https://partner.steamgames.com/doc/marketing/widget
- GitHub Pages static hosting: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- Playwright redirect-interception semantics: https://playwright.dev/python/docs/network

Implementation status is distinct from deployment status: an empty service URL means live sign-in is NOT active.

## Hosted bridge and automatic refresh (2026-10-26)

The operator deployed `https://games-steam-sync.onrender.com` on Render's free tier. The public site configuration contains only that HTTPS origin. The Steam Web API key is entered privately in Render environment settings, never in this repository or visitor storage. The health flag confirms configuration presence, not key validity or a completed real account sign-in.

An authenticated visible tab refreshes every five minutes and when returning to the tab after a minimum 65-second cooldown. The account panel includes an opt-out. Hidden/offline tabs do not automatically fetch; failures back off up to fifteen minutes. Sessions remain memory-only and expire after one hour or a server restart. This is periodic read-only synchronization, not instant push delivery or permanent background sync. Existing account-bound snapshot preservation and exact AppID matching are unchanged. Clicking a Steam store/widget control never changes local wishlist membership by assumption.

Render's free instances sleep after inactivity and can need 50 seconds or more to wake. Sign-in now checks the bridge before navigating to Valve, allowing up to 90 seconds for the wake-up. A closed or replaced sign-in attempt cannot navigate a later popup. Hosting is a single instance with manual deployments; this avoids an unreviewed GitHub account grant but does not automatically redeploy backend changes. Review and deploy backend changes separately after tests pass.

Before inviting the first real login, verify HTTPS health, exact Steam redirect/realm, secure flow-cookie flags, callback rejection without a bound flow, unauthorized sync rejection and exact-origin CORS. These checks and simulated-provider tests do not certify a real login, private-list access, universal wishlist editing or an absence of all vulnerabilities. Never request Steam passwords, session cookies, or Guard codes outside Valve's official sign-in page.
