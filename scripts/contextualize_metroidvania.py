"""Use the active genre's classification without mutating canonical shared games."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def patch(name,old,new):
 p=R/name;s=p.read_text()
 if new in s:return
 assert old in s,(name,'source anchor changed')
 p.write_text(s.replace(old,new,1))
p=R/'site/app.js';s=p.read_text()
if 'function activeGameScope(' not in s:
 marker='function recommendation(g){'
 helpers="""function activeGameScope(g){return state.hub==='Metroidvanias'?(g.metroidvaniaInfo?.structure||g.genreScope):g.genreScope;}
function activeGameCollection(g){return state.hub==='Metroidvanias'?(g.metroidvaniaCollection||g.collection):g.collection;}
function activeGameFit(g){return state.hub==='Metroidvanias'&&Object.prototype.hasOwnProperty.call(g,'metroidvaniaFit')?g.metroidvaniaFit:g.fit;}
"""
 assert marker in s;s=s.replace(marker,helpers+marker,1)
 s=s.replace("function recommendation(g){if(g.verification!=='verified'||g.fit==null||g.comingSoon)return null;let f=Number(g.fit);", "function recommendation(g){const fit=activeGameFit(g);if(g.verification!=='verified'||fit==null||g.comingSoon)return null;let f=Number(fit);",1)
 s=s.replace('if(state.scope&&g.genreScope!==state.scope)','if(state.scope&&activeGameScope(g)!==state.scope)',1)
 s=s.replace('esc(g.collection)','esc(activeGameCollection(g))')
 s=s.replace('esc(g.genreScope)','esc(activeGameScope(g))')
 s=s.replace('function why(g){','function why(g){if(state.hub===\'Metroidvanias\'&&g.metroidvaniaWhy)return g.metroidvaniaWhy;',1)
 s=s.replace('g.summary,g.curatorWhy,g.platformerWhy','g.summary,g.curatorWhy,g.metroidvaniaWhy,g.platformerWhy',1)
 s=s.replace('games.map(g=>g.genreScope).filter(Boolean)','games.flatMap(g=>[g.genreScope,g.metroidvaniaInfo?.structure]).filter(Boolean)',1)
 s=s.replace('for(const c of g.collections||[g.collection])counts.set(c,','for(const c of state.hub===\'Metroidvanias\'?[activeGameCollection(g)]:(g.collections||[g.collection]))counts.set(c,',1)
 marker=" document.body.dataset.hub='metroidvanias';"
 assert marker in s;s=s.replace(marker,marker+"\n const mvGames=games.filter(g=>(g.hubs||[]).includes('Metroidvanias'));$('#stat-collections').textContent=new Set(mvGames.map(activeGameCollection)).size;",1)
 p.write_text(s)
patch('scripts/metroidvania_model.py',"old['metroidvaniaFit']=g.get('fit');", "old['metroidvaniaFit']=g.get('fit');old['metroidvaniaWhy']=g.get('curatorWhy');")
patch('scripts/metroidvania_qa.py',"  check('Distinct exploration theme'", "  check('The sidebar contains only this genres curated shelves',page.locator('#collections [data-collection]').count()==len({g.get('metroidvaniaCollection',g['collection']) for g in rows}))\n  page.locator('[data-action=filters]').click();page.locator('#f-scope').select_option('Traditional Metroidvania');chosen=page.evaluate('GamesTest.filtered');check('Traditional style uses the active genre classification',bool(chosen) and all(by[i]['metroidvaniaInfo']['structure']=='Traditional Metroidvania' for i in chosen));page.locator('[data-action=filters]').click();page.locator('[data-hub=\"Metroidvanias\"]').click()\n  check('Distinct exploration theme'")
print('Active-genre classification, editorial fit and shelf counts are consistent.')
