/* Steam account overlay: private local snapshots, public catalog left untouched. */
'use strict';
(function installSteamSync() {
  const M = window.SteamSyncModel, STORE = 'games.steam.v1';
  const modes = { all: 'All games', owned: 'In my Steam library', wishlist: 'On my wishlist', unplayed: 'Owned, no recorded playtime', discover: 'Not in my synced library', tracked: 'Tracked in GameSync', unmatched: 'No Steam AppID' };
  const original = { filter: filterGames, render, card, table, source: sourcePanel, chips: renderChips };
  let snapshot = null, ix = M.index(null), session = null, pending = null, candidate = null;
  const refreshPolicy = window.SteamRefreshPolicy.create();
  let autoRefresh = true;
  let busy = false, epoch = 0, lastFocus = null, storageFailure = false, message = '', health = null;
  try {
    const stored = JSON.parse(localStorage.getItem(STORE) || 'null');
    if (stored) {
      snapshot = M.normalize(stored, { imported: stored.source !== 'steam', now: stored.updatedAt });
      for (const part of ['owned','wishlist']) if (stored[part]?.stale) snapshot[part] = { ...snapshot[part], stale: true, message: 'Last refresh was unavailable; showing the saved snapshot.' };
      ix = M.index(snapshot);
    }
  } catch { message = 'A saved Steam snapshot could not be read. Your ordinary library data is untouched.'; }
  defaults.steam = 'all';
  if (!Object.hasOwn(modes, state.steam)) state.steam = 'all';
  readURL(); if (!Object.hasOwn(modes, state.steam)) state.steam = 'all';
  for (const [value, text] of [['steam-hours','Steam playtime'],['steam-priority','Wishlist priority']]) $('#sort').insertAdjacentHTML('beforeend', `<option value="${value}">${text}</option>`);
  $('#main-nav').insertAdjacentHTML('beforeend', `<button class="nav-item steam-account-button" data-steam-action="open">${icon('link')}My Steam library <span class="steam-connection-dot" aria-hidden="true"></span></button>`);
  $('.heading-actions').insertAdjacentHTML('afterbegin', `<button class="quiet" data-steam-action="open">${icon('link')}Steam sync</button>`);
  $('.toolbar').insertAdjacentHTML('afterend', `<section class="steam-library-strip" aria-label="Your Steam library"><div><strong>Make this library yours.</strong><small id="steam-strip-status">Import Steam or GameSync JSON.</small></div><label><span class="sr-only">Steam library filter</span><select id="steam-filter">${Object.entries(modes).map(([k,v])=>`<option value="${k}">${esc(v)}</option>`).join('')}</select></label><button class="secondary" data-steam-action="open">Manage Steam ${icon('chevron')}</button></section>`);
  const dialog = document.createElement('dialog'); dialog.id = 'steam-sync-panel'; dialog.className = 'steam-sync-panel'; dialog.setAttribute('aria-labelledby','steam-panel-title'); document.body.append(dialog);
  function service() {
    const raw = window.GAMES_STEAM_CONFIG?.serviceUrl;
    if (!raw || location.protocol === 'file:') return null;
    try {
      const u = new URL(raw), local = ['localhost','127.0.0.1'].includes(location.hostname) && ['localhost','127.0.0.1'].includes(u.hostname);
      if ((u.protocol !== 'https:' && !(local && u.protocol === 'http:')) || u.username || u.password || u.search || u.hash || u.pathname !== '/') return null;
      return u.origin;
    } catch { return null; }
  }
  async function api(path, { method = 'GET', data, bearer, timeout = 20000 } = {}) {
    const base = service(); if (!base) throw Error('Steam sign-in needs the site operator to deploy and configure the secure bridge. Imports are available now.');
    const response = await fetch(base + path, { method, mode: 'cors', credentials: 'omit', cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(timeout),
      headers: { ...(data ? { 'Content-Type': 'application/json' } : {}), ...(bearer ? { Authorization: 'Bearer ' + bearer } : {}) }, ...(data ? { body: JSON.stringify(data) } : {}) });
    const text = await response.text(); if (text.length > 8000000) throw Error('The Steam response was too large.');
    let dataOut; try { dataOut = JSON.parse(text); } catch { throw Error('The Steam service returned an invalid response.'); }
    if (!response.ok) { if (response.status === 401 && bearer && session?.token === bearer) session = null; throw Error(typeof dataOut.message === 'string' ? dataOut.message.slice(0,300) : 'Steam sync failed; the previous snapshot is unchanged.'); }
    return dataOut;
  }
  function time(text) { return text ? new Date(text).toLocaleString() : 'Not yet synced'; }
  function save(next) {
    snapshot = next; ix = M.index(snapshot);
    try { localStorage.setItem(STORE, JSON.stringify(snapshot)); storageFailure = false; }
    catch { storageFailure = true; }
    render(); draw();
  }
  function badge(g) {
    const own = ix.owned.get(g.appid), wish = ix.wishlist.get(g.appid), tracked = ix.tracked.has(g.appid);
    const imported = snapshot?.source === 'import';
    if (!own && !wish && !tracked) return '';
    return `<div class="steam-badges">${own ? `<span class="steam-owned">${imported?'Imported library':'In Steam library'}${own.playtimeMinutes !== null ? ' &middot; '+esc((own.playtimeMinutes/60).toLocaleString(undefined,{maximumFractionDigits:1}))+' h' : ''}</span>` : ''}${wish ? '<span class="steam-wishlisted">Wishlisted</span>' : ''}${tracked ? '<span class="steam-tracked">GameSync record</span>' : ''}</div>`;
  }
  filterGames = function () {
    original.filter(); filtered = filtered.filter(g => M.match(g, state.steam, ix));
    if (state.sort === 'steam-hours') filtered.sort((a,b)=>(ix.owned.get(b.appid)?.playtimeMinutes ?? -1)-(ix.owned.get(a.appid)?.playtimeMinutes ?? -1)||a.name.localeCompare(b.name));
    if (state.sort === 'steam-priority') filtered.sort((a,b)=>(ix.wishlist.get(a.appid)?.priority ?? Infinity)-(ix.wishlist.get(b.appid)?.priority ?? Infinity)||a.name.localeCompare(b.name));
  };
  card = function (g) { return original.card(g).replace('<div class="card-body">','<div class="card-body">'+badge(g)); };
  table = function () {
    const markup = original.table(), parsed = document.createElement('template'); parsed.innerHTML = markup;
    for (const row of parsed.content.querySelectorAll('tbody tr')) {
      const g = byId.get(row.querySelector('[data-open]')?.dataset.open); if (g) row.querySelector('td')?.insertAdjacentHTML('beforeend',badge(g));
    }
    return parsed.innerHTML;
  };
  sourcePanel = function (g) {
    const own = ix.owned.get(g.appid), wish = ix.wishlist.get(g.appid), part = own ? snapshot?.owned : wish ? snapshot?.wishlist : null;
    return original.source(g) + `<section class="steam-game-brief detail-section"><h3>Your Steam snapshot</h3>${badge(g)}<p>${own ? 'This AppID is present in your '+(snapshot.source==='import'?'imported':'synced')+' library.' : wish ? 'This AppID is present in your wishlist snapshot.' : !g.appid ? 'This entry has no exact Steam AppID. Ownership on other stores is not inferred.' : 'This AppID is not in the saved Steam snapshot. That is not proof that you do not own it.'}</p>${part ? `<small>Snapshot: ${esc(time(part.checkedAt))}${part.stale?' &middot; Refresh unavailable; cached data':''}</small>` : ''}<div class="steam-detail-actions"><button class="secondary" data-steam-action="open">Manage Steam</button>${own ? `<a class="secondary" href="steam://rungameid/${M.appid(g.appid)}">Launch in Steam</a>` : ''}</div></section>`;
  };
  renderChips = function () {
    original.chips();
    const native = $('#active-filters [data-clear="steam"]'); if (native) native.remove();
    if (state.steam !== 'all') { const count=$('#filter-count');count.textContent=String(Number(count.textContent||0)+1);count.hidden=false; }
    if (state.steam !== 'all') $('#active-filters').insertAdjacentHTML('beforeend', `<button class="filter-chip" data-steam-mode="all">Steam: ${esc(modes[state.steam])} ${icon('close')}</button>`);
  };
  render = function () {
    if(!Object.hasOwn(modes,state.steam))state.steam='all';
    original.render(); $('#steam-filter').value = state.steam;
    $('#steam-filter option[value="discover"]').disabled=!ix.completeOwned;
    const ownedMatches = games.filter(g=>ix.owned.has(g.appid)).length, wishlistMatches = games.filter(g=>ix.wishlist.has(g.appid)).length;
    $('#steam-strip-status').textContent = snapshot ? `${ownedMatches} library matches / ${wishlistMatches} wishlist matches${snapshot.owned?.stale||snapshot.wishlist?.stale?' - cached after a failed refresh':''}. ${session?'Signed in.':'Saved locally.'}` : service()?'Connect Steam or import a library snapshot. Your notes stay separate.':'Import Steam or GameSync JSON. Online sign-in awaits site setup.';
    document.body.classList.toggle('steam-has-snapshot',!!snapshot);
  };
  function partView(name, part) {
    const matches = games.filter(g=>(name==='Owned games'?ix.owned:ix.wishlist).has(g.appid)).length;
    return `<article class="steam-summary-card"><small>${name}</small><strong>${part?.status==='ok'?number(part.items.length):'Unknown'}</strong><span>${part?.status==='ok'?`${matches} matches in this catalog${part.complete?'':' / partial import'}`:'Not a confirmed empty list'}</span><small>${esc(time(part?.checkedAt))}</small>${part?.stale||part?.status==='unavailable'||part?.status==='error'?`<p class="steam-warning">${esc(part.message||'Refresh unavailable; cached data retained.')}</p>`:''}</article>`;
  }
  function draw() {
    if (!dialog.open) return;
    const configured = !!service(), signed = !!session;
    dialog.innerHTML = `<header><div><span class="eyebrow">YOUR STEAM / READ-ONLY</span><h2 id="steam-panel-title">Your games. Your next discovery.</h2></div><button class="icon-button" data-steam-action="close" aria-label="Close Steam sync">${icon('close')}</button></header>
      <p class="steam-intro">See what you already have, find your wishlisted gems, and explore what is missing from your saved Steam library.</p>
      <div class="steam-account-state"><strong>${signed?'Signed in through Steam':snapshot?.source==='steam'?'Saved Steam snapshot - sign in to refresh':snapshot?'Imported snapshot - not an authenticated account':'No Steam account linked'}</strong>${snapshot?.steamId?`<a href="https://steamcommunity.com/profiles/${esc(snapshot.steamId)}" target="_blank" rel="noopener noreferrer">SteamID ${esc(snapshot.steamId)} ${icon('external')}</a>`:''}</div>
      <div class="steam-summary-grid">${partView('Owned games',snapshot?.owned)}${partView('Wishlist',snapshot?.wishlist)}</div>
      <div class="steam-actions"><button class="primary" data-steam-action="signin" ${!configured||busy||pending?'disabled':''}>${signed?'Switch Steam account':'Sign in through Steam'}</button><button class="secondary" data-steam-action="sync" ${!signed||busy?'disabled':''}>${busy?'Syncing...':'Refresh library & wishlist'}</button>${snapshot?'<button class="quiet" data-steam-action="export">Export snapshot</button>':''}${snapshot||session||pending?'<button class="quiet" data-steam-action="disconnect">Disconnect & clear Steam data</button>':''}</div>
      ${signed?`<label class="steam-import-option"><input id="steam-auto-refresh" type="checkbox" ${autoRefresh?'checked':''}> Keep this tab synced while visible (every five minutes and when returning, subject to cooldown)</label>`:''}
      <p id="steam-sync-feedback" class="steam-feedback" role="status" aria-live="polite">${esc(message||(!configured?'Online sign-in is not configured on this site yet. Local Steam and GameSync imports work below.':pending?'Complete sign-in in the Steam window.':signed?'Steam verified your identity. Sync only reads data Steam makes visible.':'Your password stays on steamcommunity.com. The service never receives it.'))}</p>
      ${health&&!health.ownedGames?'<p class="steam-warning">The bridge is reachable, but the operator must add a server-side Steam API key for owned games. Wishlist access and local imports are separate.</p>':''}
      ${storageFailure?'<p class="steam-warning">Browser storage is unavailable. This snapshot works for this tab only; export it before closing.</p>':''}
      <section class="steam-import-section"><h3>Import a Steam or GameSync snapshot</h3><p>Works without a server. Only Steam AppIDs, playtime and wishlist metadata are kept. The file is processed in this browser and is never uploaded.</p>
      <label class="steam-import-option"><input id="steam-self-reported" type="checkbox"> Treat non-wishlist GameSync records as owned (self-reported, partial list)</label>
      <label class="steam-file-label">Choose a JSON export <input id="steam-file" type="file" accept="application/json,.json" ${busy?'disabled':''}></label>
      ${candidate?`<div class="steam-import-preview"><p>Ready to import <strong>${candidate.owned.items.length} library IDs</strong>, <strong>${candidate.wishlist.items.length} wishlist IDs</strong>, and <strong>${candidate.tracked.length} tracked IDs</strong>. This does not sign you in.</p>${!candidate.steamId?'<p>This export has no verified account identity. Applying it replaces the current Steam snapshot rather than guessing which accounts to merge.</p>':''}<button class="primary" data-steam-action="import">Use this snapshot</button></div>`:''}
      <details><summary>Where do I get the file?</summary><p>First <a href="https://store.steampowered.com/login/" target="_blank" rel="noopener noreferrer">sign in on Steam</a> in this browser. Then open <a href="https://store.steampowered.com/dynamicstore/userdata/" target="_blank" rel="noopener noreferrer">their Steam store data</a> while signed in on Steam, save the JSON response, then choose it here. Steam may change this undocumented export. An empty or unavailable response is rejected.</p><p>Also accepts GetOwnedGames JSON, GetWishlist JSON, Games Steam snapshots, and GameSync exports containing <code>games</code> or <code>db.games</code>. GameSync records alone do not prove a license; unconfirmed records are labelled tracked unless you explicitly opt in above.</p><p>Never upload passwords, cookies or Steam Guard codes. A full GameSync backup can include settings; only the whitelisted game fields are retained.</p></details></section>
      <details class="steam-privacy"><summary>Privacy, coverage and site setup</summary><p>OpenID verifies your SteamID, not permission to read private lists. Set the relevant Steam game details/wishlist visibility to Public for server sync, or use a local export. Hidden, private, missing and failed lists are never silently treated as empty. Cached data is dated and can be out of date.</p><p>Matching uses exact AppIDs. Bundles, demos, DLC, family sharing, deleted licenses and other-store purchases are not inferred. Zero reported minutes is not proof a game was never played.</p><p>Your snapshot stays in this browser. The bridge holds short-lived sign-in state in memory and reads Steam on sign-in, manual refresh, and automatic refresh while this tab is visible if enabled. Automatic refresh pauses offline, backs off after failures and ends when the session expires. It is not instant push sync. Signing into Steam does not cloud-sync this site's notes. Switching accounts replaces only the Steam snapshot.</p><p>${configured?`Configured service: <code>${esc(service())}</code>. `:''}<a href="https://github.com/Herbertofury/Games/blob/main/docs/STEAM-SYNC.md" target="_blank" rel="noopener">Setup and technical details</a></p></details>`;
  }
  function open() { lastFocus=document.activeElement; candidate=null; if(!dialog.open)dialog.showModal();draw();window.dispatchEvent(new Event('lounge-overlay-change')); if(service())api('/health',{timeout:90000}).then(h=>{if(h.service!=='games-steam-sync'||h.version!==1||h.appOrigin!==location.origin)throw Error('Steam bridge configuration does not match this website.');health=h;draw();}).catch(()=>{message='The Steam bridge is not reachable or does not match this site. Your local snapshot is unchanged.';draw();}); }
  function close() { dialog.close();candidate=null;lastFocus?.focus();window.dispatchEvent(new Event('lounge-overlay-change')); }
  function random() { return btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
  async function challenge(verifier) { return btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
  function clearPending() { if(pending?.timer)clearInterval(pending.timer);pending=null; }
  async function signIn() {
    if (!service() || pending || busy) return;
    const popup=window.open('about:blank','games-steam-signin','popup,width=640,height=760');
    if(!popup){message='Allow the Steam sign-in popup, then try again.';draw();return;}
    let flow=null;
    try {
      const verifier=random(), stateToken=random(), stamp=Date.now();
      flow={popup,verifier,state:stateToken,timer:null,exchanging:false};pending=flow;
      message='Connecting to the secure Steam bridge. Free hosting may need a minute to wake...';draw();
      const ready=await api('/health',{timeout:90000});
      if(pending!==flow)return;
      if(popup.closed){clearPending();message='Steam sign-in closed. No snapshot was changed.';draw();return;}
      if(ready.service!=='games-steam-sync'||ready.version!==1||ready.appOrigin!==location.origin||ready.signIn!==true)throw Error('Steam bridge configuration does not match this website.');
      health=ready;
      const login=new URL(service()+'/auth/start');login.searchParams.set('challenge',await challenge(verifier));login.searchParams.set('client_state',stateToken);
      if(pending!==flow||popup.closed)return;
      popup.location.href=login.href;
      pending.timer=setInterval(()=>{if(!pending||pending.exchanging)return;if(popup.closed||Date.now()-stamp>600000){clearPending();message='Steam sign-in closed or expired. No snapshot was changed.';draw();}},1000);
      message='Complete sign-in on Steam. Your password and Steam Guard code stay there.';draw();
    }catch{popup.close();if(flow&&pending!==flow)return;clearPending();message='This browser could not start secure Steam sign-in. Local imports are still available.';draw();}
  }
  window.addEventListener('message',async event=>{
    const p=pending;
    if(!p||p.exchanging||event.origin!==service()||event.source!==p.popup||event.data?.type!=='games-steam-auth'||event.data.state!==p.state)return;
    p.exchanging=true;clearInterval(p.timer);
    if(event.data.error){clearPending();message='Steam sign-in was cancelled or could not be verified.';draw();return;}
    if(typeof event.data.code!=='string'||!/^[A-Za-z0-9_-]{43}$/.test(event.data.code)){clearPending();return;}
    const version=epoch;
    try {
      const result=await api('/auth/exchange',{method:'POST',data:{code:event.data.code,verifier:p.verifier}});
      if(pending!==p||epoch!==version)return;
      if(!/^[A-Za-z0-9_-]{43}$/.test(result.token))throw Error('Invalid service session.');
      const verifiedId=M.steamid(result.steamId);if(!verifiedId)throw Error('Invalid service account identity.');
      session={token:result.token,steamId:verifiedId};epoch++;refreshPolicy.reset();clearPending();
      if(!snapshot||snapshot.source!=='steam'||snapshot.steamId!==session.steamId)save(M.normalize({schemaVersion:1,provider:'steam',steamId:session.steamId},{imported:false}));
      message='Steam account verified. Reading the library and wishlist...';draw();await sync();
    }catch(error){clearPending();message=error.message;draw();}
  });
  async function sync() {
    if(!session||busy)return;const who=session,version=epoch;busy=true;refreshPolicy.started();draw();
    try {
      const raw=await api('/sync',{method:'POST',data:{},bearer:who.token});
      if(version!==epoch||session!==who)return;
      const next=M.normalize(raw,{imported:false});if(next.steamId!==who.steamId)throw Error('The sync response did not match your signed-in account.');
      save(M.merge(snapshot,next));
      refreshPolicy.finished([next.owned,next.wishlist].every(x=>x.status==='ok'));
      message=[next.owned,next.wishlist].every(x=>x.status==='ok')?'Library and wishlist refreshed. Your private notes and ratings were not changed.':'Steam did not provide every list. Available lists were updated; prior snapshots of unavailable lists were kept for the same account.';
    }catch(error){if(version===epoch&&session===who){refreshPolicy.finished(false);message=error.message||'Steam sync failed. The saved snapshot is unchanged.';}else if(version===epoch&&!session){message='Your Steam session ended. Sign in again to refresh; your saved snapshot is unchanged.';}}
    finally{busy=false;render();draw();}
  }
  async function disconnect() {
    if(!confirm('Clear only the Steam snapshot and sign-in session? Your game notes, favorites, ratings and lounge settings will remain.'))return;
    const previous=session;session=null;epoch++;refreshPolicy.reset();pending?.popup.close();clearPending();snapshot=null;ix=M.index(null);state.steam='all';candidate=null;
    try{localStorage.removeItem(STORE);}catch{storageFailure=true;}
    message='Steam data cleared. Your ordinary library and lounge settings are unchanged.';render();draw();
    if(previous)api('/logout',{method:'POST',data:{},bearer:previous.token}).catch(()=>{});
  }
  document.addEventListener('click',event=>{
    const button=event.target.closest('[data-steam-action],[data-steam-mode]');if(!button)return;
    if(button.dataset.steamMode){state.steam=button.dataset.steamMode;render();return;}
    const action=button.dataset.steamAction;
    if(action==='open')open();if(action==='close')close();if(action==='signin')signIn();if(action==='sync')sync();if(action==='disconnect')disconnect();
    if(action==='export'&&snapshot)download('Games - Steam Snapshot.json',JSON.stringify(snapshot,null,2));
    if(action==='import'&&candidate){const previous=session;session=null;epoch++;refreshPolicy.reset();pending?.popup.close();clearPending();save(M.merge(snapshot,candidate));candidate=null;message='Imported locally. No account was authenticated, and your ordinary notes were not changed.';draw();if(previous)api('/logout',{method:'POST',data:{},bearer:previous.token}).catch(()=>{});}
  });
  document.addEventListener('change',async event=>{
    if(event.target.id==='steam-auto-refresh'){autoRefresh=event.target.checked;return;}
    if(event.target.id==='steam-filter'){state.steam=event.target.value;render();}
    if(event.target.id!=='steam-file')return;
    const file=event.target.files[0],selfReported=!!$('#steam-self-reported')?.checked;if(!file)return;
    try{if(file.size>16000000)throw Error('Use a JSON export smaller than 16 MB.');candidate=M.importSnapshot(JSON.parse(await file.text()),{treatTrackedAsOwned:selfReported});message='Review the import counts before applying.';}
    catch(error){candidate=null;message=error instanceof SyntaxError?'This is not a valid JSON export.':error.message;}
    draw();
  });
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  window.addEventListener('storage',event=>{if(event.key===STORE){try{
    const raw=event.newValue?JSON.parse(event.newValue):null;
    const next=raw?M.normalize(raw,{imported:raw.source!=='steam',now:raw.updatedAt}):null;
    if(session&&(!next||next.source!=='steam'||next.steamId!==session.steamId)){session=null;epoch++;pending?.popup.close();clearPending();}
    snapshot=next;if(raw)for(const part of ['owned','wishlist'])if(raw[part]?.stale)snapshot[part]={...snapshot[part],stale:true,message:'Last refresh was unavailable; showing the saved snapshot.'};
    ix=M.index(snapshot);render();draw();
  }catch{}}});
  function maybeAutoRefresh(reason='periodic'){
    if(refreshPolicy.due({connected:!!session,visible:document.visibilityState==='visible',online:navigator.onLine!==false,busy,pending:!!pending,enabled:autoRefresh,reason}))void sync();
  }
  setInterval(()=>maybeAutoRefresh(),15000);
  window.addEventListener('focus',()=>maybeAutoRefresh('return'));
  window.addEventListener('online',()=>maybeAutoRefresh('return'));
  document.addEventListener('visibilitychange',()=>maybeAutoRefresh('return'));
  // Expose copies of membership, never credentials or a snapshot-write hook.
  window.GamesSteamContext = () => ({ steamId: snapshot?.steamId || null, owned: new Set(ix.owned.keys()), wishlist: new Set(ix.wishlist.keys()) });
  render();
})();
