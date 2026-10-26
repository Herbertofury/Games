/** Read-only Steam OpenID bridge. Node 22+, no third-party runtime packages. */
import { createServer } from 'node:http';
import { createHash, randomBytes, timingSafeEqual } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import model from '../../site/steam-model.js';

const OP = 'https://steamcommunity.com/openid/login';
const NS = 'http://specs.openid.net/auth/2.0';
const token = () => randomBytes(32).toString('base64url');
const hash = text => createHash('sha256').update(text).digest('base64url');
const safeEqual = (a, b) => typeof a === 'string' && typeof b === 'string' && a.length === b.length && timingSafeEqual(Buffer.from(a), Buffer.from(b));
const validToken = value => typeof value === 'string' && /^[A-Za-z0-9_-]{43}$/.test(value);
class Fault extends Error { constructor(status, code, message) { super(message); this.status = status; this.code = code; } }
const reject = (status, code, message) => { throw new Fault(status, code, message); };

export function configuration(env = process.env) {
  const development = env.NODE_ENV === 'development';
  const url = (value, label) => {
    let u; try { u = new URL(value); } catch { throw Error(`${label} must be an absolute URL.`); }
    const local = development && u.protocol === 'http:' && ['localhost','127.0.0.1'].includes(u.hostname);
    if ((!local && u.protocol !== 'https:') || u.username || u.password || u.search || u.hash) throw Error(`${label} must be a clean HTTPS URL.`);
    return u;
  };
  const publicUrl = url(env.PUBLIC_BASE_URL || env.RENDER_EXTERNAL_URL, 'PUBLIC_BASE_URL');
  if (publicUrl.pathname !== '/') throw Error('PUBLIC_BASE_URL must not include a path.');
  const app = url(env.APP_URL || 'https://herbertofury.github.io/Games/', 'APP_URL');
  return { publicOrigin: publicUrl.origin, appUrl: app.href, appOrigin: app.origin,
    apiKey: env.STEAM_WEB_API_KEY || '', development, maxEntries: 2000,
    authTtl: 600000, codeTtl: 60000, sessionTtl: 3600000, syncCooldown: 60000 };
}

export function createApp({ config, fetchImpl = fetch, now = Date.now } = {}) {
  if (!config) config = configuration();
  const attempts = new Map(), grants = new Map(), sessions = new Map(), nonces = new Map(), rates = new Map();
  const cookieName = config.development ? 'games_steam_login' : '__Host-games_steam_login';
  const cookie = (value, maxAge) => `${cookieName}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${maxAge}${config.development ? '' : '; Secure'}`;
  const standard = { 'Cache-Control': 'no-store, max-age=0', 'Pragma': 'no-cache', 'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY' };
  function cleanup() {
    for (const map of [attempts, grants, sessions, nonces, rates]) for (const [key, value] of map) if (value.expires <= now()) map.delete(key);
  }
  function put(map, key, value, ttl) {
    if (map.size >= config.maxEntries) reject(503, 'capacity', 'The sign-in service is busy. Please try again later.');
    map.set(key, { ...value, expires: now() + ttl });
  }
  function limit(key, maximum, period) {
    const previous = rates.get(key);
    if (previous && previous.count >= maximum) reject(429, 'rate_limited', 'Too many requests. Try again in a minute.');
    if (previous) previous.count++;
    else put(rates, key, { count: 1 }, period);
  }
  function json(value, status = 200, extra = {}) {
    return new Response(JSON.stringify(value), { status, headers: { ...standard, 'Content-Type': 'application/json; charset=utf-8', ...extra } });
  }
  function popup(payload, text = 'Steam verification finished. You can return to the Games library.') {
    const nonce = token(), encoded = JSON.stringify(payload).replace(/</g, '\\u003c');
    const body = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Games - Steam sign-in</title><body><h1>Steam sign-in</h1><p>${text}</p><p><a href="${config.appUrl}">Return to the library</a></p><script nonce="${nonce}">if(window.opener){window.opener.postMessage(${encoded},${JSON.stringify(config.appOrigin)});window.close();}</script></body></html>`;
    return new Response(body, { headers: { ...standard, 'Content-Type': 'text/html; charset=utf-8', 'Set-Cookie': cookie('', 0), 'Content-Security-Policy': `default-src 'none'; script-src 'nonce-${nonce}'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` } });
  }
  async function upstream(url, init = {}, maxBytes = 8000000) {
    const response = await fetchImpl(url, { ...init, redirect: 'error', signal: AbortSignal.timeout(12000), headers: { 'Accept': 'application/json, text/plain;q=0.9', ...init.headers } });
    if (!response.ok) reject(502, response.status === 429 ? 'steam_rate_limited' : 'steam_unavailable', 'Steam is unavailable or has limited requests. The previous snapshot is kept.');
    const reader = response.body?.getReader();
    if (!reader) reject(502, 'steam_unavailable', 'Steam returned no data.');
    const chunks = []; let size = 0;
    for (;;) {
      const { value, done } = await reader.read(); if (done) break;
      size += value.byteLength;
      if (size > maxBytes) { await reader.cancel(); reject(502, 'response_too_large', 'Steam returned an oversized response.'); }
      chunks.push(value);
    }
    return { response, text: Buffer.concat(chunks).toString('utf8') };
  }
  async function body(request) {
    if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) reject(415, 'json_required', 'Use application/json.');
    const text = await request.text();
    if (Buffer.byteLength(text) > 16384) reject(413, 'request_too_large', 'Request too large.');
    let data; try { data = JSON.parse(text); } catch { reject(400, 'invalid_json', 'Invalid JSON.'); }
    if (!data || typeof data !== 'object' || Array.isArray(data)) reject(400, 'invalid_json', 'Expected a JSON object.');
    return data;
  }
  function authenticated(request) {
    const header = request.headers.get('authorization') || '';
    const raw = header.startsWith('Bearer ') ? header.slice(7) : '';
    const session = validToken(raw) ? sessions.get(hash(raw)) : null;
    if (!session) reject(401, 'sign_in_required', 'Sign in through Steam again to refresh. Your saved snapshot is unchanged.');
    return { session, key: hash(raw) };
  }
  async function syncPart(path, params, parse, source) {
    const at = new Date(now()).toISOString();
    try {
      const url = new URL(`https://api.steampowered.com/${path}`);
      for (const [key, value] of Object.entries(params)) url.searchParams.set(key, String(value));
      const { text, response } = await upstream(url.href);
      // Some Steam services use an HTTP-200 envelope for errors/private data.
      const result = response.headers.get('x-eresult');
      if (result && result !== '1') throw Error('Steam did not make this data available.');
      return parse(JSON.parse(text), at);
    } catch (error) {
      const known = error instanceof Fault;
      return { status: 'unavailable', complete: false, checkedAt: at, source, items: [],
        message: known ? error.message : 'Steam did not provide a complete visible list. It may be private, empty without confirmation, or temporarily unavailable.' };
    }
  }
  async function route(request, clientIp) {
    const u = new URL(request.url), path = u.pathname;
    if (u.origin !== config.publicOrigin) reject(400, 'wrong_host', 'Incorrect service URL.');
    if (request.method === 'GET' && path === '/health') return json({ service: 'games-steam-sync', version: 1, signIn: true, ownedGames: !!config.apiKey, wishlist: true, appOrigin: config.appOrigin });
    if (request.method === 'GET' && path === '/auth/start') {
      limit('login:' + hash(clientIp), 20, 600000);
      if ([...u.searchParams.keys()].some(k => u.searchParams.getAll(k).length !== 1)) reject(400, 'duplicate_parameter', 'Duplicate sign-in parameter.');
      const challenge = u.searchParams.get('challenge'), clientState = u.searchParams.get('client_state');
      if (!validToken(challenge) || !validToken(clientState)) reject(400, 'invalid_start', 'Start sign-in from the Games library.');
      const state = token(), cookieSecret = token();
      const returnTo = `${config.publicOrigin}/auth/callback?state=${state}`;
      put(attempts, state, { challenge, clientState, cookieHash: hash(cookieSecret), returnTo }, config.authTtl);
      const login = new URL(OP);
      for (const [k,v] of Object.entries({ ns: NS, mode: 'checkid_setup', identity: NS + '/identifier_select', claimed_id: NS + '/identifier_select', return_to: returnTo, realm: config.publicOrigin + '/' })) login.searchParams.set('openid.' + k, v);
      return new Response(null, { status: 302, headers: { ...standard, Location: login.href, 'Set-Cookie': cookie(cookieSecret, config.authTtl / 1000) } });
    }
    if (request.method === 'GET' && path === '/auth/callback') {
      const state = u.searchParams.get('state'), attempt = attempts.get(state);
      const rawCookie = (request.headers.get('cookie') || '').split(';').map(s => s.trim()).find(s => s.startsWith(cookieName + '='))?.slice(cookieName.length + 1);
      if (!attempt || !validToken(rawCookie) || !safeEqual(hash(rawCookie), attempt.cookieHash)) reject(400, 'login_expired', 'This sign-in expired or did not start in this browser. Return to the library and try again.');
      attempts.delete(state); // one attempt, including concurrent callbacks
      try {
        for (const key of u.searchParams.keys()) if (u.searchParams.getAll(key).length !== 1) reject(400, 'duplicate_parameter', 'Duplicate OpenID parameter.');
        const p = name => u.searchParams.get('openid.' + name);
        if (p('mode') === 'cancel') return popup({ type: 'games-steam-auth', state: attempt.clientState, error: 'Sign-in was cancelled.' }, 'Sign-in was cancelled. No account was linked.');
        if (p('ns') !== NS || p('mode') !== 'id_res' || ![OP, 'https://steamcommunity.com/openid/'].includes(p('op_endpoint'))) reject(400, 'invalid_assertion', 'Invalid Steam assertion.');
        if (p('return_to') !== attempt.returnTo || p('identity') !== p('claimed_id')) reject(400, 'invalid_assertion', 'Steam identity or return URL did not match.');
        const identity = /^https?:\/\/steamcommunity\.com\/openid\/id\/(\d{17})$/.exec(p('claimed_id') || '');
        if (!identity) reject(400, 'invalid_identity', 'Invalid Steam identity.');
        const steamId = model.steamid(identity[1]);
        const signed = new Set((p('signed') || '').split(','));
        for (const field of ['op_endpoint','claimed_id','identity','return_to','response_nonce','assoc_handle']) if (!signed.has(field)) reject(400, 'unsigned_field', 'A required OpenID field was not signed.');
        if (!p('sig') || !p('assoc_handle')) reject(400, 'invalid_signature', 'Missing Steam signature.');
        const nonce = p('response_nonce') || '', time = Date.parse(nonce.slice(0,20));
        if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ.+$/.test(nonce) || nonce.length > 255 || !Number.isFinite(time) || now() - time > 300000 || time - now() > 60000 || nonces.has(nonce)) reject(400, 'nonce_rejected', 'Steam assertion expired or was already used.');
        put(nonces, nonce, {}, 600000);
        const check = new URLSearchParams();
        for (const [key, value] of u.searchParams) if (key.startsWith('openid.')) check.set(key, value);
        check.set('openid.mode', 'check_authentication');
        const { text } = await upstream(OP, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: check.toString() }, 16384);
        const lines = text.replace(/\r/g,'').split('\n');
        if (lines.filter(x => x === 'is_valid:true').length !== 1 || lines.some(x => x.startsWith('is_valid:') && x !== 'is_valid:true')) reject(401, 'steam_rejected', 'Steam did not validate this sign-in.');
        const code = token(); put(grants, hash(code), { steamId, challenge: attempt.challenge }, config.codeTtl);
        return popup({ type: 'games-steam-auth', state: attempt.clientState, code });
      } catch {
        return popup({ type: 'games-steam-auth', state: attempt.clientState, error: 'Steam sign-in could not be verified. Please try again.' }, 'Steam sign-in could not be verified. No account was linked.');
      }
    }
    // All data-bearing requests require the one configured frontend origin.
    if (request.headers.get('origin') !== config.appOrigin) reject(403, 'origin_rejected', 'This origin is not authorized.');
    if (request.method === 'POST' && path === '/auth/exchange') {
      limit('exchange:' + hash(clientIp), 30, 60000);
      const data = await body(request);
      if (!validToken(data.code) || !validToken(data.verifier)) reject(400, 'invalid_exchange', 'Invalid sign-in exchange.');
      const key = hash(data.code), grant = grants.get(key);
      if (!grant || !safeEqual(hash(data.verifier), grant.challenge)) reject(401, 'invalid_exchange', 'Sign-in exchange failed.');
      grants.delete(key);
      const bearer = token(); put(sessions, hash(bearer), { steamId: grant.steamId, lastSync: null, busy: false }, config.sessionTtl);
      return json({ token: bearer, steamId: grant.steamId, expiresAt: new Date(now() + config.sessionTtl).toISOString() });
    }
    if (request.method === 'POST' && path === '/logout') {
      const { key } = authenticated(request); sessions.delete(key); return json({ signedOut: true });
    }
    if (request.method === 'POST' && path === '/sync') {
      const { session } = authenticated(request); await body(request);
      if (session.busy || (session.lastSync !== null && now() - session.lastSync < config.syncCooldown)) reject(429, 'cooldown', 'Refresh is limited to once per minute. Your saved snapshot is unchanged.');
      limit('sync:' + session.steamId, 10, 600000);
      session.busy = true; session.lastSync = now();
      try {
        const [owned, wishlist] = await Promise.all([
          config.apiKey ? syncPart('IPlayerService/GetOwnedGames/v1/', { key: config.apiKey, input_json: JSON.stringify({ steamid: session.steamId, include_appinfo: false, include_played_free_games: true }) }, model.ownedResponse, 'steam-web-api') : Promise.resolve({ status: 'unavailable', complete: false, items: [], message: 'The site operator has not configured the server-side Steam API key. Local imports still work.' }),
          syncPart('IWishlistService/GetWishlist/v1/', { steamid: session.steamId }, model.wishlistResponse, 'steam-wishlist-service')
        ]);
        return json({ schemaVersion: 1, provider: 'steam', steamId: session.steamId, updatedAt: new Date(now()).toISOString(), owned, wishlist, tracked: [] });
      } finally { session.busy = false; }
    }
    reject(404, 'not_found', 'Not found.');
  }
  return async function handle(request, { clientIp = 'local' } = {}) {
    cleanup();
    const origin = request.headers.get('origin');
    const cors = origin === config.appOrigin ? { 'Access-Control-Allow-Origin': config.appOrigin, 'Vary': 'Origin', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Authorization, Content-Type' } : {};
    try {
      if (request.method === 'OPTIONS') {
        if (origin !== config.appOrigin) reject(403, 'origin_rejected', 'Origin not authorized.');
        return new Response(null, { status: 204, headers: { ...standard, ...cors } });
      }
      const response = await route(request, clientIp);
      for (const [key, value] of Object.entries(cors)) response.headers.set(key, value);
      return response;
    } catch (error) {
      const known = error instanceof Fault;
      return json({ error: known ? error.code : 'service_error', message: known ? error.message : 'The Steam service could not complete this request. Please try again.' }, known ? error.status : 500, { ...cors, ...(error.status === 429 ? { 'Retry-After': '60' } : {}) });
    }
  };
}

export function serve(config = configuration()) {
  const handle = createApp({ config });
  const server = createServer({ maxHeaderSize: 16384, requestTimeout: 20000, headersTimeout: 10000 }, async (req, res) => {
    try {
      let size = 0; const chunks = [];
      for await (const chunk of req) {
        size += chunk.length;
        if (size > 16384) { res.writeHead(413, { 'Cache-Control': 'no-store' }); res.end('Request too large'); return; }
        chunks.push(chunk);
      }
      const request = new Request(new URL(req.url, config.publicOrigin), { method: req.method, headers: req.headers,
        ...(['GET','HEAD'].includes(req.method) ? {} : { body: Buffer.concat(chunks) }) });
      const response = await handle(request, { clientIp: req.socket.remoteAddress || 'unknown' });
      res.writeHead(response.status, Object.fromEntries(response.headers)); res.end(Buffer.from(await response.arrayBuffer()));
    } catch { res.writeHead(400, { 'Cache-Control': 'no-store' }); res.end('Invalid request'); }
  });
  server.listen(Number(process.env.PORT || 8789), '0.0.0.0', () => console.log('Steam read-only bridge started. Credentials and request URLs are not logged.'));
  return server;
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) serve();
