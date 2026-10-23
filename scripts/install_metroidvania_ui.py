"""Idempotent assertion-guarded integration with the existing living library."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def patch(name,old,new):
 p=R/name;s=p.read_text()
 if new in s:return
 assert old in s,(name,'source anchor changed')
 p.write_text(s.replace(old,new,1))
protected=R/'data/metroidvania-protected.json'
if not protected.exists():
 d=json.loads((R/'data/catalog.json').read_text());protected.write_text(json.dumps({'ids':[g['id'] for g in d['items'] if 'Metroidvanias' not in g.get('hubs',[])],'hubCounts':d['build']['hubCounts']},indent=2)+'\n')
patch('scripts/catalog_model.py',"    out=sorted(games.values(),key=lambda g:g['name'].casefold())","    from metroidvania_model import integrate\n    mv=integrate(ROOT,games)\n    out=sorted(games.values(),key=lambda g:g['name'].casefold())")
patch('scripts/catalog_model.py',"    c['generatedAt']=max(dates) if dates else None","    if mv.get('generatedAt'):dates.append(mv['generatedAt'])\n    c['generatedAt']=max(dates) if dates else None")
patch('scripts/catalog_model.py',"    b['hubCounts']=","    b['generator']='games-catalog/1.4.0'\n    b['candidateUnresolved']+=mv['unresolved']\n    b['candidateDispositions']+=mv['dispositions']\n    b['metroidvaniaCount']=len(mv['ids'])\n    b['hubCounts']=")
patch('scripts/build.py',"    build_wiki(ROOT,catalog)","    build_wiki(ROOT,catalog)\n    from metroidvania_wiki import build as build_metroidvania_wiki\n    build_metroidvania_wiki(ROOT,catalog)")
patch('scripts/build.py',"'version':'1.3.0'","'version':'1.4.0'")
patch('site/index.html','Real-time strategy <span class="new-pill">NEW</span></button></nav>','Real-time strategy</button><button class="nav-item" data-hub="Metroidvanias">Metroidvanias <span class="new-pill">NEW</span></button></nav>')
patch('site/index.html','<div class="rts-command-strip" hidden>','<div class="mv-explore-strip" hidden><span>THE EXPLORATION ATLAS / 04</span><strong>Every locked door is a promise.</strong><small>Discover the world. Change how you move. Return transformed.</small></div><div class="rts-command-strip" hidden>')
patch('site/index.html','<span>GO DEEPER</span>','<span>GO DEEPER</span><button data-preset="mv-dark" class="mv-only" hidden>Dark castles</button><button data-preset="mv-puzzle" class="mv-only" hidden>Puzzle labyrinths</button><button data-preset="mv-3d" class="mv-only" hidden>3D exploration</button><button data-preset="mv-free" class="mv-only" hidden>Free mini-vanias</button><button data-preset="mv-hidden" class="mv-only" hidden>Hidden gems</button><button data-preset="mv-watchlist" class="mv-only" hidden>Upcoming worlds</button>')
patch('site/app.js','g.name,g.seedName,g.summary','g.name,g.seedName,...(g.aliases||[]),g.summary')
patch('site/app.js','g.rtsInfo?.skirmish,...g.tags','g.rtsInfo?.skirmish,g.metroidvaniaInfo?.structure,g.metroidvaniaInfo?.traversal,...g.tags')
patch('site/app.js',"state.hub==='Real-time strategy'?2732960:state.hub==='Boomer shooters'?3115160:2218750","state.hub==='Metroidvanias'?1030300:state.hub==='Real-time strategy'?2732960:state.hub==='Boomer shooters'?3115160:2218750")
patch('site/app.js',"$('#hero-summary').textContent=state.hub==='Real-time strategy'?","$('#hero-summary').textContent=state.hub==='Metroidvanias'?'A world that opens with every new ability. Hidden paths, unforgettable bosses, and one more room worth discovering.':state.hub==='Real-time strategy'?")
patch('site/app.js',"if(name==='torment'){if(state.hub==='Real-time strategy')","if(name==='torment'){if(state.hub==='Metroidvanias'){state.tag='MV core';}else if(state.hub==='Real-time strategy')")
patch('site/app.js',"if(name==='demos'){if(state.hub==='Real-time strategy')","if(name==='demos'){if(['Real-time strategy','Metroidvanias'].includes(state.hub))")
patch('site/app.js',"if(state.hub==='Real-time strategy')state.tag='Recent RTS release';}render();","if(state.hub==='Real-time strategy')state.tag='Recent RTS release';if(state.hub==='Metroidvanias')state.tag='Recent Metroidvania release';}if(name==='mv-dark'){state.tag='MV dark fantasy';state.playable=true;}if(name==='mv-puzzle'){state.tag='MV puzzle-led';state.playable=true;}if(name==='mv-3d'){state.tag='MV 3D';state.playable=true;}if(name==='mv-free'){state.free=true;state.playable=true;}if(name==='mv-hidden'){state.hidden=true;state.playable=true;}if(name==='mv-watchlist'){state.status='Upcoming';state.sort='newest';}render();")
patch('site/app.js','${rtsBrief(g)}${g.kind?','${rtsBrief(g)}${metroidvaniaBrief(g)}${g.kind?')
p=R/'site/app.js';s=p.read_text()
if 'function renderBaseHub()' not in s:
 s=s.replace('function renderHub(){','function renderBaseHub(){',1)
 s+='''
function renderHub(){
 const changed=renderedHub!==state.hub+'|'+(CATALOG.build?.datasetHash||games.length);
 renderBaseHub();if(!changed)return;
 const mv=state.hub==='Metroidvanias';
 $$('.mv-only,.mv-explore-strip').forEach(n=>n.hidden=!mv);
 const mods=$('[data-preset="mods"]');if(mods)mods.hidden=mv;
 if(!mv)return;
 document.body.dataset.hub='metroidvanias';
 $('.intro h1').innerHTML='Get beautifully lost<span>.</span>';
 $('.intro p').textContent='A new ability. An old doorway. An entirely new world. The essentials, the hidden gems, and the discoveries waiting beyond Steam.';
 $('.feature-pill').innerHTML=icon('spark')+' THE WORLD BEYOND THE NEXT DOOR';
 $('.feature-index strong').textContent='04 / THE METROIDVANIA COLLECTION';
 const t=$('[data-preset="torment"]');t.querySelector('strong').textContent='The exploration feeling';t.querySelector('small').textContent='Connected worlds. Meaningful upgrades.';
}
function metroidvaniaBrief(g){
 if(!(g.hubs||[]).includes('Metroidvanias'))return '';
 const m=g.metroidvaniaInfo||{};
 return `<div class="mv-brief"><span>EXPLORER'S BRIEF</span><div><section><small>WORLD STRUCTURE</small><strong>${esc(m.structure||g.genreScope||'See game description')}</strong></section><section><small>STORE-DESCRIBED MECHANICS</small><strong>${esc(m.traversal||'See the official description')}</strong></section></div><p>${esc(m.basis||'Editorial genre classification; source details are linked below.')}</p>${g.recommendationCaution?`<p class="recommendation-caution">${esc(g.recommendationCaution)}</p>`:''}${g.originalReleaseYear?`<p>Original release: ${esc(g.originalReleaseYear)}. Store dates may describe a later edition.</p>`:''}${g.aliases?.length?`<details><summary>Also searchable as / included games</summary><p>${esc(g.aliases.join(', '))}</p></details>`:''}${g.comingSoon?'<p>Watchlist only. Any playable demo is a distinct build, not the released full game.</p>':''}</div>`;
}
'''
 p.write_text(s)
p=R/'site/styles.css';s=p.read_text()
if '/* Metroidvania exploration atlas */' not in s:
 s+='''
/* Metroidvania exploration atlas */
body[data-hub="metroidvanias"]{--accent:#c8b7ff;--accent-strong:#e3d9ff;--accent-dim:rgba(200,183,255,.12);--accent-soft:rgba(200,183,255,.09)}
body[data-hub="metroidvanias"] .intro h1{font-size:clamp(34px,4vw,58px);letter-spacing:-.05em}
body[data-hub="metroidvanias"] .featured{border-color:rgba(200,183,255,.23);background:#191425}
body[data-hub="metroidvanias"] .feature-art{opacity:.8;filter:saturate(.9)}
body[data-hub="metroidvanias"] .feature-noise{background:linear-gradient(90deg,rgba(20,15,32,.97),rgba(20,15,32,.73) 45%,rgba(20,15,32,.13))}
body[data-hub="metroidvanias"] .featured:before{background:linear-gradient(0deg,rgba(20,15,32,.55),transparent)}
body[data-hub="metroidvanias"] .feature-content{max-width:660px}
.mv-explore-strip{display:flex;align-items:center;gap:22px;margin:26px 0 15px;padding:16px 19px;border:1px solid var(--border);border-left:2px solid var(--accent);border-radius:0 12px 12px 0;background:linear-gradient(100deg,rgba(200,183,255,.075),transparent)}
.mv-explore-strip>span{font-size:9px;letter-spacing:.14em;color:var(--accent);font-weight:800}.mv-explore-strip>strong{font-size:12px}.mv-explore-strip>small{margin-left:auto;color:var(--muted);font-size:10px;max-width:240px;line-height:1.5}
.mv-only[hidden],.mv-explore-strip[hidden],[data-preset="mods"][hidden]{display:none!important}
.mv-brief{margin:22px 0;padding:21px;border:1px solid var(--border);border-radius:12px;background:rgba(200,183,255,.04)}.mv-brief>span{color:var(--accent);font-size:10px;font-weight:800;letter-spacing:.16em}.mv-brief>div{display:grid;grid-template-columns:1fr 1fr;gap:25px;margin-top:18px}.mv-brief small{display:block;color:var(--muted);font-size:9px;letter-spacing:.1em;margin-bottom:8px}.mv-brief strong{font-size:13px;line-height:1.6}.mv-brief p{font-size:11px;line-height:1.7;color:var(--muted);margin-top:15px}.mv-brief summary{cursor:pointer;font-size:11px}
body.light[data-hub="metroidvanias"]{--accent:#7052ba;--accent-strong:#51398f}body.light[data-hub="metroidvanias"] .featured{--accent:#d4c5ff;color:#f5f2ff}
@media(max-width:700px){.mv-explore-strip{flex-wrap:wrap;gap:9px}.mv-explore-strip>small{width:100%;max-width:none;margin:0}.mv-brief>div{grid-template-columns:1fr}.mv-explore-strip>strong{font-size:11px}body[data-hub="metroidvanias"] .feature-content{padding:25px}body[data-hub="metroidvanias"] .intro h1{font-size:39px}}
'''
 p.write_text(s)
patch('tests/test_rts.py',"self.assertEqual(len(self.rows),130);self.assertEqual(len(self.data['items']),448);self.assertEqual(len({g['id'] for g in self.data['items']}),448)","self.assertEqual(len(self.rows),130);self.assertGreaterEqual(len(self.data['items']),448);self.assertEqual(len({g['id'] for g in self.data['items']}),len(self.data['items']));protected=json.loads((R/'data/metroidvania-protected.json').read_text());self.assertTrue(set(protected['ids']) <= {g['id'] for g in self.data['items']})")
print('Metroidvania model, wiki, UI and protected-identity checks integrated.')
