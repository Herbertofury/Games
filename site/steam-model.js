/* Shared, dependency-free Steam snapshot validation. Never accepts credentials. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SteamSyncModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const MAX_ITEMS = 50000;
  const object = x => !!x && typeof x === 'object' && !Array.isArray(x);
  function appid(x) {
    if (typeof x !== 'number' && typeof x !== 'string') throw Error('An AppID must be a number.');
    if (!/^\d+$/.test(String(x))) throw Error('Invalid Steam AppID.');
    const n = Number(x);
    if (!Number.isSafeInteger(n) || n < 1 || n > 4294967295) throw Error('Invalid Steam AppID.');
    return n;
  }
  function steamid(x) {
    if (x === null || x === undefined || x === '') return null;
    if (typeof x !== 'string' || !/^\d{17}$/.test(x)) throw Error('SteamID64 must be a 17-digit string, not a rounded number.');
    const n = BigInt(x), base = 76561197960265728n;
    if (n < base || n > base + 4294967295n) throw Error('Not an individual SteamID64.');
    return x;
  }
  function integer(x, max = 100000000) {
    if (x === null || x === undefined) return null;
    if (typeof x !== 'number' || !Number.isSafeInteger(x) || x < 0 || x > max) throw Error('Invalid playtime, date, or rank.');
    return x;
  }
  function stamp(x, fallback) {
    return typeof x === 'string' && x.length < 40 && Number.isFinite(Date.parse(x)) ? new Date(x).toISOString() : fallback;
  }
  function items(rows, kind) {
    if (!Array.isArray(rows) || rows.length > MAX_ITEMS) throw Error('Expected a bounded list of Steam games.');
    const seen = new Map();
    for (const raw of rows) {
      const r = object(raw) ? raw : { appid: raw };
      const id = appid(r.appid);
      const item = { appid: id };
      if (kind === 'owned') {
        item.playtimeMinutes = integer(r.playtimeMinutes ?? r.playtime_forever);
        item.lastPlayed = integer(r.lastPlayed ?? r.rtime_last_played, 10000000000);
      } else if (kind === 'wishlist') {
        item.priority = integer(r.priority);
        item.addedAt = integer(r.addedAt ?? r.date_added, 10000000000);
      }
      seen.set(id, item);
    }
    return [...seen.values()].sort((a, b) => a.appid - b.appid);
  }
  function ownedResponse(raw, checkedAt = new Date().toISOString()) {
    const r = raw?.response;
    if (!object(r) || !Number.isInteger(r.game_count) || r.game_count < 0 || r.game_count > MAX_ITEMS)
      throw Error('Steam did not return a visible library. It may be private or unavailable.');
    const rows = r.games === undefined && r.game_count === 0 ? [] : r.games;
    const out = items(rows, 'owned');
    if (out.length !== r.game_count || rows.length !== out.length) throw Error('Steam returned an incomplete library; the previous snapshot is kept.');
    return { status: 'ok', complete: true, checkedAt, source: 'steam-web-api', items: out };
  }
  function wishlistResponse(raw, checkedAt = new Date().toISOString()) {
    if (!object(raw?.response) || !Array.isArray(raw.response.items))
      throw Error('Steam did not return a wishlist. An absent list is not treated as empty.');
    const out = items(raw.response.items, 'wishlist');
    if (out.length !== raw.response.items.length) throw Error('Steam returned duplicate wishlist IDs.');
    return { status: 'ok', complete: true, checkedAt, source: 'steam-wishlist-service', items: out };
  }
  function component(raw, kind, now, imported) {
    if (!object(raw)) return { status: 'unknown', complete: false, items: [] };
    if (raw.status !== 'ok') return { status: ['unavailable','error','unknown'].includes(raw.status) ? raw.status : 'unknown', complete: false, items: [], message: String(raw.message || 'No snapshot available.').slice(0,240) };
    return { status: 'ok', complete: raw.complete === true, checkedAt: stamp(raw.checkedAt, now), source: imported ? 'local-import' : String(raw.source || 'steam').slice(0,60), items: items(raw.items, kind) };
  }
  function normalize(raw, { imported = true, now = new Date().toISOString() } = {}) {
    if (!object(raw) || raw.schemaVersion !== 1 || raw.provider !== 'steam') throw Error('Unsupported Steam snapshot version.');
    const out = { schemaVersion: 1, provider: 'steam', steamId: steamid(raw.steamId), source: imported ? 'import' : 'steam', updatedAt: now,
      owned: component(raw.owned, 'owned', now, imported), wishlist: component(raw.wishlist, 'wishlist', now, imported), tracked: items(raw.tracked || [], 'tracked') };
    return out;
  }
  function importSnapshot(raw, { treatTrackedAsOwned = false, now = new Date().toISOString() } = {}) {
    if (!object(raw)) throw Error('Import a JSON object, not a list or a web page.');
    if (raw.provider === 'steam' && raw.schemaVersion === 1) {
      const clean = normalize(raw, { now });
      if (clean.owned.status !== 'ok' && clean.wishlist.status !== 'ok' && !clean.tracked.length) throw Error('This snapshot contains no available Steam list. The current snapshot is kept.');
      return clean;
    }
    const out = { schemaVersion: 1, provider: 'steam', steamId: null, source: 'import', updatedAt: now,
      owned: { status: 'unknown', complete: false, items: [] }, wishlist: { status: 'unknown', complete: false, items: [] }, tracked: [] };
    if (Array.isArray(raw.rgOwnedApps) || Array.isArray(raw.rgWishlist)) {
      if (!(raw.rgOwnedApps?.length || raw.rgWishlist?.length) && raw.bLoggedIn !== true) throw Error('Steam returned empty browser data without a signed-in confirmation. Your previous snapshot is kept.');
      if (Array.isArray(raw.rgOwnedApps)) out.owned = { status: 'ok', complete: true, checkedAt: now, source: 'steam-browser-export', items: items(raw.rgOwnedApps, 'owned') };
      if (Array.isArray(raw.rgWishlist)) out.wishlist = { status: 'ok', complete: true, checkedAt: now, source: 'steam-browser-export', items: items(raw.rgWishlist, 'wishlist') };
    } else if (object(raw.response) && Object.hasOwn(raw.response, 'game_count')) out.owned = { ...ownedResponse(raw, now), source: 'local-import' };
    else if (Array.isArray(raw.response?.items)) out.wishlist = { ...wishlistResponse(raw, now), source: 'local-import' };
    else {
      // GameSync exports are library records, not proof of a Steam license.
      const db = object(raw.db?.games) ? raw.db.games : object(raw.games) ? raw.games : null;
      if (!db) throw Error('No supported Steam or GameSync library was found. Export JSON, not credentials or cookies.');
      const records = Object.values(db);
      if (records.length > MAX_ITEMS) throw Error('The export is too large.');
      const wishlist = [], tracked = [], owned = [];
      for (const g of records) {
        if (!object(g)) continue;
        const source = Array.isArray(g.sources) ? g.sources.find(s => object(s) && s.platform === 'steam') : null;
        const key = /^steam:(\d+)$/.exec(String(g.key || ''));
        const id = g.platform === 'steam' ? g.platformId : source?.platformId || key?.[1];
        if (!id) continue;
        const aid = appid(id);
        if (['wishlist','wishlisted','wanttoplay'].includes(String(g.status || '').toLowerCase())) wishlist.push({ appid: aid });
        else if (treatTrackedAsOwned || g.owned === true) {
          const minutes = typeof g.hoursPlayed === 'number' && g.hoursPlayed >= 0 && g.hoursPlayed < 1000000 ? Math.round(g.hoursPlayed * 60) : null;
          owned.push({ appid: aid, playtimeMinutes: minutes });
        } else tracked.push({ appid: aid });
      }
      if (!wishlist.length && !owned.length && !tracked.length) throw Error('No Steam AppIDs were found in this GameSync export.');
      out.wishlist = { status: 'ok', complete: false, checkedAt: now, source: 'gamesync-import', items: items(wishlist, 'wishlist') };
      if (owned.length) out.owned = { status: 'ok', complete: false, checkedAt: now, source: 'gamesync-self-reported', items: items(owned, 'owned') };
      out.tracked = items(tracked, 'tracked');
    }
    return out;
  }
  function merge(previous, next) {
    const same = previous && previous.steamId === next.steamId && previous.source === next.source;
    const out = { ...next };
    if (same) for (const key of ['owned','wishlist']) {
      if (next[key].status !== 'ok' && previous[key]?.status === 'ok')
        out[key] = { ...previous[key], stale: true, lastAttemptAt: next.updatedAt, message: next[key].message || 'Refresh unavailable; showing the previous snapshot.' };
      else if (next[key].status === 'ok' && !next[key].complete && previous[key]?.status === 'ok')
        out[key] = { ...next[key], complete: false, items: items([...previous[key].items, ...next[key].items], key) };
    }
    return out;
  }
  function index(snapshot) {
    const map = key => new Map((snapshot?.[key]?.items || []).map(x => [x.appid, x]));
    return { owned: map('owned'), wishlist: map('wishlist'), tracked: new Set((snapshot?.tracked || []).map(x => x.appid)), completeOwned: snapshot?.owned?.status === 'ok' && snapshot.owned.complete === true };
  }
  function match(game, mode, ix) {
    if (!mode || mode === 'all') return true;
    let id; try { id = appid(game.appid); } catch { return mode === 'unmatched'; }
    if (mode === 'owned') return ix.owned.has(id);
    if (mode === 'wishlist') return ix.wishlist.has(id);
    if (mode === 'unplayed') return ix.owned.get(id)?.playtimeMinutes === 0;
    if (mode === 'discover') return ix.completeOwned && !ix.owned.has(id);
    if (mode === 'tracked') return ix.tracked.has(id);
    return false;
  }
  return { MAX_ITEMS, appid, steamid, items, ownedResponse, wishlistResponse, normalize, importSnapshot, merge, index, match };
});
