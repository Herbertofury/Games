/* Couch multiplayer: exact headcounts intersect with the same selected mode. */
'use strict';
(function installPartyHub(){
 const HUB='Couch co-op & party',WIKI='https://github.com/Herbertofury/Games/wiki/';
 const active=()=>state.hub===HUB;
 const prior={scope:activeGameScope,collection:activeGameCollection,fit:activeGameFit,feature:featuredGame,hero,hub:renderHub,preset,source:sourcePanel,why,card,table,filter:filterGames,sync:syncControls,chips:renderChips,compare:openCompare,query:queryMatches,export:exportData};
 const setups={simultaneous:'Same-screen / split-screen',phones:'Phones as controllers',hotseat:'Pass-the-pad / hotseat',asymmetric:'VR / asymmetric setup'};
 let hubKey=null;
 function countsText(counts){
  const xs=[...new Set(counts||[])].sort((a,b)=>a-b);if(!xs.length)return 'Count needs confirmation';
  if(xs.length===1)return String(xs[0]);
  if(xs.every((n,i)=>!i||n===xs[i-1]+1))return xs[0]+'\u2013'+xs.at(-1);
  return xs.join(' or ');
 }
 function modesFor(g,mode=state.partyMode,baseOnly=state.partyBaseOnly){return (g.partyInfo?.modesDetail||[]).filter(m=>(!mode||m.type===mode)&&(!baseOnly||!m.requiresDlc));}
 function matches(g,params=state){
  const p=g.partyInfo;if(!p)return false;
  if(params.partySetup&&p.participation!==params.partySetup)return false;
  if(params.partyEdition==='pc'&&!/PC|Windows|Linux|macOS/i.test(p.platform||''))return false;
  if(params.partyEdition==='console'&&/PC|Windows|Linux|macOS/i.test(p.platform||''))return false;
  const ms=modesFor(g,params.partyMode,params.partyBaseOnly);
  if((params.partyMode||params.partyBaseOnly)&&!ms.length)return false;
  if(params.partyPlayers){
   const nums=ms.flatMap(m=>m.counts||[]);
   if(params.partyPlayers==='5plus'){if(!nums.some(n=>n>=5))return false;}
   else if(params.partyPlayers==='9plus'){if(!nums.some(n=>n>=9))return false;}
   else if(params.partyPlayers==='unknown'){if(nums.length)return false;}
   else if(!nums.includes(Number(params.partyPlayers)))return false;
  }
  return true;
 }
 function badges(g){const p=g.partyInfo;if(!p)return '';const visibleModes=modesFor(g),visibleCounts=[...new Set(visibleModes.flatMap(m=>m.counts||[]))];return `<div class="party-badges"><span class="party-player-badge" title="${esc(p.platform)}">${icon('people')} ${esc(countsText(visibleCounts))}${visibleCounts.length?' local':''}</span>${[...new Set(visibleModes.map(m=>m.type))].map(m=>`<span class="party-mode-badge">${esc(m==='Versus'?'Versus / teams':'Co-op')}</span>`).join('')}${p.participation!=='simultaneous'?`<span class="party-setup-badge">${esc(setups[p.participation]||p.participation)}</span>`:''}${(p.modesDetail||[]).some(m=>m.requiresDlc)?'<span class="party-setup-badge">Some modes need DLC</span>':''}</div>`;}
 ICONS.people='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M15 3a4 4 0 0 1 0 8M22 21v-2a4 4 0 0 0-3-3.87M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0';
 if(!document.querySelector('[data-hub="'+HUB+'"]'))$('.genre-hubs').insertAdjacentHTML('beforeend',`<button class="nav-item" data-hub="${HUB}">Couch co-op &amp; party <span class="new-pill">NEW</span></button>`);
 $('.featured').insertAdjacentHTML('afterend',`<section class="party-lobby" hidden aria-labelledby="party-lobby-title"><div class="party-lobby-heading"><div><span class="eyebrow">BUILD YOUR GAME NIGHT</span><h2 id="party-lobby-title">Same room. Different kinds of chaos.</h2><p>Choose the people, then the rules. No online limits disguised as couch-player counts.</p></div><a class="quiet" href="${WIKI}Couch-Coop-and-Party" target="_blank" rel="noopener">The party atlas ${icon('external')}</a></div><div class="party-controls"><label><span>WHO'S ON THE COUCH?</span><select id="party-players"><option value="">Any group size</option>${[2,3,4,5,6,7,8].map(n=>`<option value="${n}">${n} people</option>`).join('')}<option value="5plus">5+ people</option><option value="9plus">9+ people</option><option value="unknown">Count needs confirmation</option></select></label><label><span>TEAM UP OR FACE OFF?</span><select id="party-mode"><option value="">Co-op + competitive</option><option value="Co-op">Cooperate against the game</option><option value="Versus">Versus / team-versus</option></select></label><label><span>HOW YOU PLAY</span><select id="party-setup"><option value="">Any local setup</option>${Object.entries(setups).map(([v,t])=>`<option value="${v}">${esc(t)}</option>`).join('')}</select></label><label><span>EDITION</span><select id="party-edition"><option value="">PC + console discoveries</option><option value="pc">PC editions</option><option value="console">Console editions</option></select></label></div><div class="party-lobby-footer"><label class="party-dlc-check"><input id="party-base-only" type="checkbox"> Only modes that do not need extra DLC</label><button class="quiet" data-party-reset>Reset party filters</button></div><nav class="party-routes" aria-label="Game-night shortcuts"><button data-party-route="favorites">Your kind of chaos</button><button data-party-route="duo">Two-person teamwork</button><button data-party-route="four">Four controllers</button><button data-party-route="crowd">Five or more</button><button data-party-route="new">Fresh party picks</button><button data-party-route="hidden">Hidden gems</button><button data-party-route="phones">Bring your phones</button><button data-party-route="free">Free discoveries</button><button data-party-route="upcoming">On the radar</button></nav></section>`);
 activeGameScope=g=>active()?(g.partyScope||g.genreScope):prior.scope(g);
 activeGameCollection=g=>active()?(g.partyCollection||g.collection):prior.collection(g);
 activeGameFit=g=>active()&&g.partyFit!=null?g.partyFit:prior.fit(g);
 why=g=>active()&&g.partyWhy?g.partyWhy:prior.why(g);
 queryMatches=function(g,q){
  const tokens=q.match(/(?:[^\s"]+|"[^"]*")+/g)||[];const special=tokens.filter(t=>/^players:\d+$|^mode:(coop|versus)$/i.test(t));
  if(special.length){const query={partyPlayers:'',partyMode:'',partyBaseOnly:false};for(const t of special){const [k,v]=t.toLowerCase().split(':');if(k==='players')query.partyPlayers=v;else query.partyMode=v==='coop'?'Co-op':'Versus';}if(!matches(g,query))return false;}
  return prior.query(g,tokens.filter(t=>!special.includes(t)).join(' '));
 };
 filterGames=function(){const coop=state.coop;if(active())state.coop=false;prior.filter();state.coop=coop;if(active()){filtered=filtered.filter(g=>matches(g)&&(!coop||g.partyInfo?.modesDetail.some(m=>m.type==='Co-op')));if(state.sort==='players')filtered.sort((a,b)=>(b.partyInfo?.localMax||0)-(a.partyInfo?.localMax||0)||(recommendation(b)||0)-(recommendation(a)||0));}};
 card=function(g){let html=prior.card(g);if(!active())return html;return html.replace('<p class="card-description">',badges(g)+'<p class="card-description">').replace(/> Trailer<\/button>/g,'> Watch</button>');};
 table=function(){
  if(!active())return prior.table();
  return `<table class="party-table"><thead><tr><th><button data-sort="name">Game / collection</button></th><th><button data-sort="players">Local people</button></th><th>Co-op / versus limits</th><th>Setup / edition</th><th><button data-sort="recommended">For you</button></th><th><button data-sort="rating">Community reception</button></th><th><button data-sort="newest">Release</button></th><th>Compare</th><th>Save</th><th>Source</th></tr></thead><tbody>${filtered.map(g=>{const p=g.partyInfo;return `<tr><td><button class="table-name" data-open="${esc(g.id)}">${img(g.image,'')}<span><strong>${esc(g.name)}</strong><small>${esc(activeGameCollection(g))}</small></span></button></td><td><strong>${esc(countsText(p.playerCounts))}</strong></td><td>${p.modes.map(m=>`${esc(m)}: ${esc(countsText(p.modesDetail.filter(x=>x.type===m).flatMap(x=>x.counts)))}`).join('<br>')}${p.modesDetail.some(m=>m.requiresDlc)?'<small>Some capacity requires DLC</small>':''}</td><td>${esc(setups[p.participation]||p.participation)}<small>${esc(p.platform)}</small></td><td>${recommendation(g)??'Watchlist'}${recommendation(g)!=null?' / 10':''}</td><td>${esc(ratingText(g))}<small>${esc(reviewText(g))}</small></td><td>${esc(date(g))}<small>${esc(g.status)}</small></td><td><input type="checkbox" data-compare="${esc(g.id)}" ${compare.has(g.id)?'checked':''} aria-label="Compare ${esc(g.name)}"></td><td><button data-save="${esc(g.id)}" aria-label="Save ${esc(g.name)}" aria-pressed="${prefs.favorites.includes(g.id)}">${icon(prefs.favorites.includes(g.id)?'check':'heart')}</button></td><td><a href="${esc(projectURL(g))}" target="_blank" rel="noopener" aria-label="Open ${esc(g.name)}">${icon('external')}</a></td></tr>`;}).join('')}</tbody></table>`;
 };
 exportData=function(format){
  if(!active()||format!=='csv')return prior.export(format);
  const header=['Game','Party collection','Local player counts','Local co-op counts','Local versus counts','Mode-specific limits and conditions','Participation','Edition','Inputs / hardware','Connectivity note','Recommendation /10','Steam positive %','Review count','Release','Status','Official URL','All confirmed stores','Personal rating','Play status','Notes'];
  const rows=[header,...filtered.map(g=>{const p=g.partyInfo;return [g.name,activeGameCollection(g),countsText(p.playerCounts),countsText(p.coopCounts),countsText(p.versusCounts),p.modesDetail.map(m=>m.name+': '+countsText(m.counts)+'; '+m.type+(m.requiresDlc?'; additional DLC required':'')+(m.notes?'; '+m.notes:'')).join(' | '),setups[p.participation],p.platform,p.inputs,p.requiresInternet,recommendation(g),g.rating,g.reviewCount,g.releaseDate||g.releaseLabel,g.status,projectURL(g),g.storefronts.map(l=>l.provider+' ['+l.kind+']: '+l.url).join(' | '),prefs.ratings[g.id],prefs.statuses[g.id],prefs.notes[g.id]];})];
  download('Games - Party Collection.csv','\ufeff'+rows.map(r=>r.map(csvCell).join(',')).join('\r\n'),'text/csv;charset=utf-8');toast('Exported '+filtered.length+' games with local-mode details.');
 };
 featuredGame=function(){return active()?(byId.get('steam:965680')||games.find(g=>g.hubs.includes(HUB))):prior.feature();};
 hero=function(){prior.hero();if(active()){$('#hero-summary').textContent='Boomerang Fu is the starting point, not the finish line. Find your next Lethal League obsession, a two-person adventure, or the game that gets the whole room shouting.';}};
 renderHub=function(){
  const changed=renderedHub!==state.hub+'|'+(CATALOG.build?.datasetHash||games.length);prior.hub();$('.party-lobby').hidden=!active();
  let option=$('#sort option[value="players"]');if(active()&&!option)$('#sort').insertAdjacentHTML('beforeend','<option value="players">Most local players</option>');if(option)option.hidden=!active();
  if(!active()){hubKey=null;return;}
  document.body.dataset.hub='party';$('.intro h1').innerHTML='One more round<span>.</span>';$('.intro p').textContent='Good friends. Great rivalries. The finest couch co-op, ridiculous party battles, and under-the-radar local multiplayer.';
  $('.feature-pill').innerHTML=icon('spark')+' YOUR KIND OF CHAOS';$('.feature-index strong').textContent='08 / THE COUCH MULTIPLAYER COLLECTION';
  const t=$('[data-preset="torment"]');t.querySelector('strong').textContent='The Lethal League feeling';t.querySelector('small').textContent='Fast rounds. Big reads. Instant rematches.';
  $('[data-preset="best"] small').textContent='The strongest matches for your game night.';$('[data-preset="new"] small').textContent='Recent games, not old games with a new patch.';$('[data-preset="mods"]').hidden=true;
  const key=state.hub+'|'+CATALOG.build.datasetHash;
  if(changed||hubKey!==key){const counts=new Map();for(const g of games.filter(g=>g.hubs.includes(HUB))){const c=activeGameCollection(g);counts.set(c,(counts.get(c)||0)+1);}$('#stat-collections').textContent=counts.size;$('#collections').innerHTML=[...counts].sort((a,b)=>a[0].localeCompare(b[0])).map(([c,n])=>`<button class="nav-item collection-link" data-collection="${esc(c)}"><span class="collection-dot"></span>${esc(c)}<b>${n}</b></button>`).join('');hubKey=key;}
  $$('.genre-hubs [data-hub]').forEach(b=>b.classList.toggle('active',b.dataset.hub===HUB));
 };
 syncControls=function(){prior.sync();$('#party-players').value=state.partyPlayers;$('#party-mode').value=state.partyMode;$('#party-setup').value=state.partySetup;$('#party-edition').value=state.partyEdition;$('#party-base-only').checked=!!state.partyBaseOnly;};
 renderChips=function(){prior.chips();if(!active())return;const root=$('#active-filters');if(!root)return;for(const [k,label]of [['partyPlayers','People'],['partyMode','Mode'],['partySetup','Setup'],['partyEdition','Edition'],['partyBaseOnly','Base game only']])if(state[k])root.insertAdjacentHTML('beforeend',`<button class="filter-chip" data-party-clear="${k}">${esc(label+': '+(typeof state[k]==='boolean'?'Yes':setups[state[k]]||state[k]))} ${icon('close')}</button>`);const n=root.querySelectorAll('.filter-chip').length;$('#filter-count').textContent=n;$('#filter-count').hidden=!n;};
 sourcePanel=function(g){
  const html=prior.source(g);if(!g.partyInfo)return html;const p=g.partyInfo;
  return html+`<section class="party-brief detail-section"><span class="eyebrow">GAME-NIGHT DOSSIER</span><h3>${esc(countsText(p.playerCounts))}${p.playerCounts.length?' local people':''}</h3><p>${esc(g.partyWhy||g.summary)}</p><div class="party-facts"><div><small>EXACT EDITION</small><strong>${esc(p.platform)}</strong></div><div><small>PARTICIPATION</small><strong>${esc(setups[p.participation]||p.participation)}</strong></div><div><small>INPUTS / HARDWARE</small><strong>${esc(p.inputs)}</strong></div><div><small>CONNECTIVITY</small><strong>${esc(p.requiresInternet||'Local support does not by itself guarantee offline operation.')}</strong></div></div><div class="party-mode-list">${p.modesDetail.map(m=>`<article><div><strong>${esc(m.name)}</strong><span>${esc(m.type==='Versus'?'Versus / teams':m.type)}</span></div><b>${esc(countsText(m.counts))}${m.counts.length?' people':''}</b>${m.notes?`<p>${esc(m.notes)}</p>`:''}<a href="${esc(safeURL(m.sourceUrl))}" target="_blank" rel="noopener">${esc(m.evidenceBasis||'Mode source')} ${icon('external')}</a></article>`).join('')}</div>${p.notes?`<p class="party-caution">${esc(p.notes)}</p>`:''}<p class="party-boundary">${esc(p.basis)}</p><a href="${WIKI}Party-Player-Guide" target="_blank" rel="noopener">How to read player counts and editions ${icon('external')}</a></section>`;
 };
 openCompare=function(){prior.compare();const gs=[...compare].map(id=>byId.get(id)).filter(Boolean);if(gs.length<2)return;$$('.compare-column').forEach((node,i)=>{const p=gs[i]?.partyInfo;if(!p)return;node.insertAdjacentHTML('beforeend',`<div class="compare-field party-compare"><small>LOCAL PLAYERS / EDITION</small><strong>${esc(countsText(p.playerCounts))} / ${esc(p.platform)}</strong></div><div class="compare-field"><small>MODE-SPECIFIC CAPACITY</small>${p.modesDetail.map(m=>`<strong>${esc(m.name)}: ${esc(countsText(m.counts))}${m.requiresDlc?' (extra DLC)':''}</strong>`).join('')}</div><div class="compare-field"><small>LOCAL SETUP</small><strong>${esc(setups[p.participation]||p.participation)}</strong></div>`);});};
 function route(name){
  state={...defaults,hub:HUB,view:state.view};
  if(name==='favorites'){state.tag='Disc Jam / Lethal League feeling';state.playable=true;}
  if(name==='duo'){state.partyPlayers='2';state.partyMode='Co-op';state.partySetup='simultaneous';state.playable=true;}
  if(name==='four'){state.partyPlayers='4';state.partySetup='simultaneous';state.playable=true;}
  if(name==='crowd'){state.partyPlayers='5plus';state.partySetup='simultaneous';state.playable=true;}
  if(name==='new'){state.tag='Recent couch release';state.playable=true;state.sort='newest';}
  if(name==='hidden'){state.hidden=true;state.playable=true;}
  if(name==='phones'){state.partySetup='phones';state.playable=true;}
  if(name==='free'){state.free=true;state.playable=true;}
  if(name==='upcoming'){state.status='Upcoming';state.sort='newest';}
  if(name==='best'){state.fit=8;state.playable=true;}
  if(name==='outside')state.offSteam=true;
  if(name==='demos')state.demo=true;
  render();$('#library').scrollIntoView({block:'start',behavior:'smooth'});
 }
 preset=function(name){if(!active())return prior.preset(name);const map={torment:'favorites',best:'best',new:'new',outside:'outside',demos:'demos',watchlist:'upcoming'};return map[name]?route(map[name]):prior.preset(name);};
 document.addEventListener('change',e=>{const fields={'party-players':'partyPlayers','party-mode':'partyMode','party-setup':'partySetup','party-edition':'partyEdition','party-base-only':'partyBaseOnly'},key=fields[e.target.id];if(key){state[key]=typeof defaults[key]==='boolean'?e.target.checked:e.target.value;render();}});
 document.addEventListener('click',e=>{const routeButton=e.target.closest('[data-party-route]');if(routeButton)return route(routeButton.dataset.partyRoute);const clear=e.target.closest('[data-party-clear]');if(clear){state[clear.dataset.partyClear]=defaults[clear.dataset.partyClear];return render();}if(e.target.closest('[data-party-reset]')){for(const k of ['partyPlayers','partyMode','partySetup','partyEdition','partyBaseOnly'])state[k]=defaults[k];render();}});
 window.PartyTest={matches,countsText,modesFor};
 renderedHub=undefined;options();render();hero();if(currentGame)openGame(currentGame.id);
})();
