/* Platformer extension: shares the canonical data, controls and personal state. */
'use strict';
(function installPlatformerHub(){
 const hub='Platformers';
 const wiki='https://github.com/Herbertofury/Games/wiki/Platformers';
 const originalBestLabel=$('[data-preset="best"] small').textContent,originalNewLabel=$('[data-preset="new"] small').textContent;
 const featuredBefore=featuredGame,heroBefore=hero,renderHubBefore=renderHub,presetBefore=preset,sourceBefore=sourcePanel,cardBefore=card;
 let primaryRoutesKey=null;
 if(!document.querySelector('[data-hub="Platformers"]'))document.querySelector('.genre-hubs').insertAdjacentHTML('beforeend','<button class="nav-item" data-hub="Platformers">Platformers <span class="new-pill">NEW</span></button>');
 document.querySelector('.featured').insertAdjacentHTML('afterend',`<section class="platformer-guide" hidden aria-label="Platformer study routes"><div><span class="eyebrow">MOVEMENT IS THE POINT / 04</span><h2>Find your kind of leap.</h2><p>Precision classics, expressive 3D worlds, cinematic puzzles, co-op discoveries and the gems between them.</p></div><nav aria-label="Platformer routes"><button data-platformer-route="precision">Precision & mastery</button><button data-platformer-route="3d">3D worlds</button><button data-platformer-route="exploration">Exploration</button><button data-platformer-route="puzzles">Puzzles & atmosphere</button><button data-platformer-route="coop">Bring a friend</button><button data-platformer-route="gems">Gem shortlist</button><button data-platformer-route="free">Free creator games</button><button data-platformer-route="upcoming">Upcoming, not yet rated</button></nav><a class="quiet platformer-study-link" href="${wiki}" target="_blank" rel="noopener">Read the full study, source notes and illustrated dossiers ${icon('external')}</a></section>`);
 featuredGame=function(){return state.hub===hub?(games.find(g=>g.appid===504230&&g.verification==='verified')||games.find(g=>(g.hubs||[]).includes(hub))):featuredBefore();};
 hero=function(){heroBefore();if(state.hub===hub)$('#hero-summary').textContent='One dash. A thousand possibilities. Start with Celeste, then follow the movement into unfamiliar worlds, overlooked gems and the next generation of platformers.';};
 card=function(g){return cardBefore(state.hub===hub&&g.platformerCollection?{...g,collection:g.platformerCollection}:g);};
 renderHub=function(){
  const baseInvalidated=renderedHub!==state.hub+'|'+(CATALOG.build?.datasetHash||games.length);
  renderHubBefore();const active=state.hub===hub;
  $('.platformer-guide').hidden=!active;
  if(!active){primaryRoutesKey=null;$('[data-preset="best"] small').textContent=originalBestLabel;$('[data-preset="new"] small').textContent=originalNewLabel;return;}
  // Each record has one primary platformer route. Other genre memberships
  // remain on the canonical object but do not inflate this hub's navigation.
  const key=CATALOG.build?.datasetHash||String(games.length);
  if(primaryRoutesKey!==key||baseInvalidated){
   const scoped=games.filter(g=>(g.hubs||[]).includes(hub));
   $('#stat-collections').textContent=new Set(scoped.map(g=>g.platformerCollection)).size;
   renderCollections(scoped.map(g=>({...g,collections:[g.platformerCollection]})));
   primaryRoutesKey=key;
  }
  document.body.dataset.hub='platformers';
  $('.intro h1').innerHTML='Make the leap<span>.</span>';
  $('.intro p').textContent='The platformer study. Precision classics, expressive 3D worlds, cinematic puzzles, co-op discoveries and the gems between them.';
  $('.feature-pill').innerHTML=icon('spark')+' THE MOVEMENT BENCHMARK';
  $('.feature-index strong').textContent='04 / THE PLATFORMER COLLECTION';
  const gem=$('[data-preset="torment"]');gem.querySelector('strong').textContent='Beyond the obvious';gem.querySelector('small').textContent='Reviewed gem leads. Distinctive movement.';
  $('[data-preset="best"] small').textContent='Strong editorial fit; reception still matters.';
  $('[data-preset="new"] small').textContent='Newest playable releases and editions';
  $$('.genre-hubs [data-hub]').forEach(n=>n.classList.toggle('active',n.dataset.hub===state.hub));
 };
 preset=function(name){
  if(state.hub!==hub)return presetBefore(name);
  if(!['torment','best','new','watchlist','demos','outside'].includes(name))return presetBefore(name);
  state={...defaults,hub,view:state.view};
  if(name==='torment'){state.tag='Platformer gem shortlist';state.playable=true;}
  if(name==='best'){state.fit=8;state.playable=true;}
  if(name==='new'){state.sort='newest';state.playable=true;}
  if(name==='watchlist'){state.status='Upcoming';state.sort='newest';}
  if(name==='demos')state.demo=true;
  if(name==='outside')state.offSteam=true;
  render();$('#library').scrollIntoView({block:'start',behavior:'smooth'});
 };
 sourcePanel=function(g){
  const base=sourceBefore(g);if(!(g.hubs||[]).includes(hub))return base;
  const p=g.platformerInfo||{};
  return base+`<section class="platformer-brief detail-section"><span class="eyebrow">PLATFORMER FIELD NOTES</span><h3>${esc(p.focus||g.platformerCollection||g.collection)}</h3><p>${esc(g.platformerWhy||g.curatorWhy||g.summary)}</p><div class="platformer-facts"><div><small>SCOPE</small><strong>${esc(p.scope||'See the exact source edition')}</strong></div><div><small>VERIFIED HARDWARE / BUILDS</small><strong>${esc((g.platforms||[]).join(' / ')||'See official page')}</strong></div></div><p class="recommendation-caution">${esc(g.platformerCaution||g.recommendationCaution||'Check the exact store edition and current requirements.')}</p><small>${esc(p.selectionBasis||'Source-grounded editorial selection, not a hands-on playtest claim.')} ${esc(p.platformScope||'')}</small><p><a href="${wiki}" target="_blank" rel="noopener">Study methodology and comparison routes</a></p></section>`;
 };
 document.addEventListener('click',e=>{
  const b=e.target.closest('[data-platformer-route]');if(!b)return;
  const route=b.dataset.platformerRoute;state={...defaults,hub,view:state.view};
  const collections={precision:'Precision & mastery','3d':'3D worlds & collectathons',exploration:'Exploration & Metroidvanias',puzzles:'Puzzles & cinematic journeys',coop:'Co-op & playful chaos',free:'Free creator releases'};
  if(collections[route])state.collection=collections[route];
  if(route==='gems'){state.tag='Platformer gem shortlist';state.playable=true;}
  if(route==='upcoming'){state.status='Upcoming';state.sort='newest';}
  render();$('#library').scrollIntoView({block:'start',behavior:'smooth'});
 });
 renderedHub=undefined;options();render();hero();if(currentGame)openGame(currentGame.id);
})();
