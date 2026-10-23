/* Survival extension: one canonical library, two deliberately distinct homes. */
'use strict';
(function installSurvivalHubs(){
 const hubs=['Survival','Minecraft-like worlds'];
 const wiki='https://github.com/Herbertofury/Games/wiki/';
 const config={
  Survival:{theme:'survival',title:'Make a place in the wild',intro:'Gather. Build. Explore. The Conan, ARK and Windrose feeling, from shared-world adventures to small survival discoveries.',index:'06 / THE SURVIVAL COLLECTION',eyebrow:'THE NEXT GREAT EXPEDITION',hero:'Sails on the horizon. A home worth defending. Start with Windrose, then discover the next world you will make your own.',page:'Survival',atlas:'Survival-Media',anchor:3041230,core:'Conan / ARK / Windrose feeling'},
  'Minecraft-like worlds':{theme:'voxel',title:'A world worth making your own',intro:'Mine deeper. Build stranger. Make it yours. A separate home for Minecraft, Terraria, Hytale, Vintage Story and their most interesting neighbors.',index:'07 / THE MINECRAFT-LIKE COLLECTION',eyebrow:'ONE BLOCK. ENDLESS POSSIBILITIES.',hero:'A campfire becomes a home. A handful of stones becomes a civilization. Explore deeper survival, 2D sandboxes and the next wave of block-built worlds.',page:'Minecraft-Like-Worlds',atlas:'Minecraft-Like-Media',anchor:'external:vintage-story',core:'Survival core'}
 };
 const before={scope:activeGameScope,collection:activeGameCollection,fit:activeGameFit,feature:featuredGame,hero,hub:renderHub,preset,source:sourcePanel,why,card};
 const active=()=>hubs.includes(state.hub);let routeKey=null;
 for(const hub of hubs)if(!document.querySelector('[data-hub="'+hub+'"]'))$('.genre-hubs').insertAdjacentHTML('beforeend',`<button class="nav-item" data-hub="${esc(hub)}">${esc(hub)} <span class="new-pill">NEW</span></button>`);
 $('.featured').insertAdjacentHTML('afterend',`<section class="survival-guide" hidden aria-label="Survival discovery routes"><div class="survival-guide-heading"><div><span class="eyebrow">CHOOSE YOUR NEXT WORLD</span><h2 id="survival-guide-title">An expedition, not just a checklist.</h2><p id="survival-guide-copy">The right world depends on how you like to survive.</p></div><a class="quiet" id="survival-wiki" href="${wiki}Survival" target="_blank" rel="noopener">Full illustrated guide ${icon('external')}</a></div><nav aria-label="Survival routes"><button data-survival-route="core">Closest matches</button><button data-survival-route="playable">Playable now</button><button data-survival-route="coop">Build with friends</button><button data-survival-route="solo">Solo listed</button><button data-survival-route="new">Fresh discoveries</button><button data-survival-route="gems">Hidden gems</button><button data-survival-route="free">Free worlds</button><button data-survival-route="outside">Beyond Steam</button><button data-survival-route="demos">Playable demos</button><button data-survival-route="upcoming">Upcoming worlds</button><button data-survival-route="2d" class="voxel-route">Terraria-like 2D</button><button data-survival-route="blocks" class="voxel-route">Block-building survival</button><button data-survival-route="mods" class="voxel-route">Modding mentioned</button></nav><p class="survival-boundary">Single-player does not automatically mean offline. Co-op does not automatically mean cross-play. Exact editions and source evidence are in each game's field notes.</p></section>`);
 activeGameScope=g=>active()?(g.survivalScope||g.genreScope):before.scope(g);
 activeGameCollection=g=>active()?(g.survivalCollection||g.collection):before.collection(g);
 activeGameFit=g=>active()&&Object.prototype.hasOwnProperty.call(g,'survivalFit')?g.survivalFit:before.fit(g);
 why=g=>active()&&g.survivalWhy?g.survivalWhy:before.why(g);
 card=g=>{const text=before.card(g);return active()?text.replace(/> Trailer<\/button>/g,'> Watch</button>'):text;};
 featuredGame=function(){if(!active())return before.feature();const id=config[state.hub].anchor;return games.find(g=>(typeof id==='string'?g.id===id:g.appid===id)&&g.verification==='verified')||games.find(g=>g.hubs.includes(state.hub));};
 hero=function(){before.hero();if(active())$('#hero-summary').textContent=config[state.hub].hero;};
 renderHub=function(){
  const baseInvalidated=renderedHub!==state.hub+'|'+(CATALOG.build?.datasetHash||games.length);
  before.hub();$('.survival-guide').hidden=!active();
  if(!active()){routeKey=null;return;}
  const c=config[state.hub],isVoxel=state.hub===hubs[1];document.body.dataset.hub=c.theme;
  $('.intro h1').innerHTML=esc(c.title)+'<span>.</span>';$('.intro p').textContent=c.intro;
  $('.feature-pill').innerHTML=icon('spark')+' '+esc(c.eyebrow);$('.feature-index strong').textContent=c.index;
  $('#survival-guide-title').textContent=isVoxel?'Not every blocky world is the same.':'Choose the way you want to survive.';
  $('#survival-guide-copy').textContent=isVoxel?'Block survival, Terraria-like sandboxes and clearly labelled creative neighbors.':'Persistent bases, wilderness pressure, mobile homes and unmistakably different neighbors.';
  $('#survival-wiki').href=wiki+c.page;
  $$('.voxel-route').forEach(n=>n.hidden=!isVoxel);
  const t=$('[data-preset="torment"]');t.querySelector('strong').textContent=isVoxel?'The Minecraft-like feeling':'The Conan / ARK feeling';t.querySelector('small').textContent=isVoxel?'Mining, crafting and worlds you reshape.':'A base, a crew, a world worth exploring.';
  $('[data-preset="best"] small').textContent='Strong fit, with reception and sample sizes visible.';
  $('[data-preset="new"] small').textContent='Recent first releases; old editions stay labelled.';
  $('[data-preset="mods"]').hidden=true;
  const key=state.hub+'|'+CATALOG.build.datasetHash;
  if(routeKey!==key||baseInvalidated){
   const scoped=games.filter(g=>g.hubs.includes(state.hub)),counts=new Map();for(const g of scoped){const col=activeGameCollection(g);counts.set(col,(counts.get(col)||0)+1);}
   $('#stat-collections').textContent=counts.size;
   $('#collections').innerHTML=[...counts].sort((a,b)=>a[0].localeCompare(b[0])).map(([col,n])=>`<button class="nav-item collection-link" data-collection="${esc(col)}"><span class="collection-dot"></span>${esc(col)}<b>${n}</b></button>`).join('');routeKey=key;
  }
  $$('.genre-hubs [data-hub]').forEach(n=>n.classList.toggle('active',n.dataset.hub===state.hub));
 };
 function route(name){
  const hub=state.hub;state={...defaults,hub,view:state.view};
  if(name==='core'){state.tag=config[hub].core;state.playable=true;}
  if(name==='playable')state.playable=true;
  if(name==='coop'){state.coop=true;state.playable=true;}
  if(name==='solo'){state.tag='Single-player listed';state.playable=true;}
  if(name==='new'){state.tag='Recent survival release';state.playable=true;state.sort='newest';}
  if(name==='gems'){state.hidden=true;state.playable=true;}
  if(name==='free'){state.free=true;state.playable=true;}
  if(name==='outside')state.offSteam=true;
  if(name==='demos')state.demo=true;
  if(name==='upcoming'){state.status='Upcoming';state.sort='newest';}
  if(name==='2d'){state.tag='Terraria-like worlds';state.playable=true;}
  if(name==='blocks'){state.tag='Block-building survival';state.playable=true;}
  if(name==='mods'){state.tag='Modding mentioned';state.playable=true;}
  if(name==='best'){state.fit=8;state.playable=true;}
  render();$('#library').scrollIntoView({block:'start',behavior:'smooth'});
 }
 preset=function(name){if(!active())return before.preset(name);const map={torment:'core',best:'best',new:'new',outside:'outside',demos:'demos',watchlist:'upcoming'};if(map[name])return route(map[name]);return before.preset(name);};
 sourcePanel=function(g){
  const base=before.source(g);if(!g.survivalInfo)return base;const s=g.survivalInfo;
  const fields=[['WORLD & SYSTEMS',s.world],['SOLO',s.solo],['CO-OP',s.coop],['HOSTING',s.hosting],['MODDING',s.modding],['TERRAIN & BUILDING',s.terrain]];
  return base+`<section class="survival-brief detail-section"><span class="eyebrow">SURVIVAL FIELD NOTES</span><h3>${esc(g.survivalCollection||g.collection)}</h3><p>${esc(g.survivalWhy||g.summary)}</p><div class="survival-facts">${fields.map(([label,value])=>`<div><small>${esc(label)}</small><strong>${esc(value||'Check the official source')}</strong></div>`).join('')}</div><p class="survival-boundary">${esc(s.basis)}</p>${g.originalReleaseYear?`<p>Original release: ${esc(g.originalReleaseYear)}. The store date may describe a later edition or full-release milestone.</p>`:''}${g.recommendationCaution?`<p class="recommendation-caution">${esc(g.recommendationCaution)}</p>`:''}<a href="${wiki}Survival-Field-Guide" target="_blank" rel="noopener">Edition, server and source guide ${icon('external')}</a></section>`;
 };
 document.addEventListener('click',e=>{const b=e.target.closest('[data-survival-route]');if(b&&active())route(b.dataset.survivalRoute);});
 renderedHub=undefined;options();render();hero();if(currentGame)openGame(currentGame.id);
})();
