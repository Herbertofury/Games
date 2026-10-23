"""Platformer integration, editorial overlays and reproducible coverage metadata."""
from __future__ import annotations
import copy, csv, json, pathlib
HUB='Platformers'
ADJACENT={
 'Crypt Custodian':'Top-down exploration with platforming elements',
 'Noita':'Physics-simulation action roguelite / traversal hybrid',
 'Rain World':'Ecosystem-survival platformer',
 'Portal':'First-person spatial puzzle / traversal hybrid',
 'Portal 2':'First-person spatial puzzle / traversal hybrid',
 'Supraland':'First-person puzzle-exploration platformer',
 'Supraland Six Inches Under':'First-person puzzle-exploration platformer',
 'Supraworld':'First-person puzzle-exploration platformer',
 'Neon White':'First-person speedrunning shooter / platformer',
 'Ghostrunner':'First-person combat / parkour platformer',
 'Ghostrunner 2':'First-person combat / parkour platformer',
 'Boomerang X':'Aerial arena combat / platformer hybrid',
 'Echo Point Nova':'Open-world shooter / traversal hybrid',
 'Luna Abyss':'First-person cinematic shooter / platformer hybrid',
 'Denshattack!':'Vehicle-trick action / traversal hybrid',
 'Laika: Aged Through Blood':'Motorcycle action-exploration hybrid',
 "Yoku's Island Express":'Pinball exploration-platformer hybrid',
 'A Short Hike':'Gentle climbing and gliding adventure',
 'Lil Gator Game':'Gentle exploration adventure with traversal',
 'Gecko Gods':'Climbing-led puzzle-exploration adventure',
 'PEAK':'Cooperative climbing / survival traversal',
 'Getting Over It with Bennett Foddy':'Physics-climbing mastery challenge',
 'A Difficult Game About Climbing':'Physics-climbing mastery challenge',
 'Anodyne 2: Return to Dust':'3D exploration and 2D adventure hybrid',
 'The House of Hikmah':'Narrative puzzle-adventure with traversal',
 'HUNTDOWN':'Run-and-gun action platformer',
 'Blazing Chrome':'Run-and-gun action platformer',
 'Iron Meat':'Run-and-gun action platformer',
 'Katana ZERO':'Cinematic action platformer',
 'Spiritfall':'Platform-fighter-inspired action roguelite',
}

def read(root,path,default):
 p=root/path
 return json.loads(p.read_text()) if p.exists() else default

def source_sets(root):
 return [read(root,'data/platformers-steam.json',{'items':[],'unresolved':[]}),read(root,'data/platformers-external.json',{'items':[]})]

def notes(root):
 p=root/'data/platformers-editorial.tsv'
 return {r['name']:r for r in csv.DictReader(p.open(),delimiter='\t')} if p.exists() else {}

def merge_platformers(games,root):
 """One stable record per game. Existing shooter/RTS facts win on overlap."""
 root=pathlib.Path(root);editorial=notes(root)
 for data in source_sets(root):
  for item in data['items']:
   raw=copy.deepcopy(item);ident=raw['id'];seed=raw.get('seedName',raw['name'])
   prior=games.get(ident)
   collision=bool(prior and not prior.get('platformerManaged',False) and any(h!=HUB for h in prior.get('hubs',[])))
   g=prior if collision else raw
   if not collision:g['platformerManaged']=True
   g['hubs']=list(dict.fromkeys(g.get('hubs',[])+[HUB]+(['Roguelites'] if raw['collection']=='Roguelite platformers' else [])))
   g['collections']=list(dict.fromkeys(g.get('collections',[g['collection']])+[raw['collection']]))
   g['tags']=sorted(set(g.get('tags',[])+raw.get('tags',[])+['Platformer']))
   g['platformerCollection']=raw['collection']
   info=copy.deepcopy(raw.get('platformerInfo',{}))
   info['focus']=ADJACENT.get(seed,raw.get('genreScope',raw['collection']))
   info['scope']='Explicit hybrid / adjacent route' if seed in ADJACENT else 'Core platformer or platforming-led exploration'
   info['selectionBasis']='Source-grounded editorial analysis, not a claim of hands-on playtesting.'
   info['sourceUrl']=raw.get('primaryUrl') or raw.get('steamUrl')
   note=editorial.get(seed) or editorial.get(raw['name'])
   g['platformerWhy']=note['why'] if note else raw.get('curatorWhy',raw.get('summary',''))
   g['platformerCaution']=note['caution'] if note else raw.get('recommendationCaution',raw.get('requirements',''))
   info['editorialDepth']='Individual editorial note' if note or not raw.get('steamUrl') else 'Subgenre study lens; see official description and verified facts'
   if raw.get('comingSoon'):
    if not collision:g['fit']=None
    g['platformerCaution']='Upcoming / watchlist only. No current purchase recommendation. '+g['platformerCaution']
   if seed in ADJACENT and not collision:g['genreScope']=info['focus']
   g['platformerInfo']=info
   if not collision:
    g['curatorWhy']=g['platformerWhy']
    g['recommendationCaution']=g['platformerCaution']
    # Editorial discovery leads are not automatically confirmed hidden gems.
    g['hiddenGem']=bool(raw.get('hiddenGem') and not raw.get('comingSoon') and (raw.get('fit') or 0)>=8 and not raw.get('reviewError') and 30<=raw.get('reviewCount',0)<=5000 and (raw.get('rating') or 0)>=80)
   if g.get('hiddenGem'):g['tags']=sorted(set(g['tags']+['Platformer gem shortlist']))
   if not raw.get('comingSoon') and (raw.get('releaseDate') or '')>='2025-01-01':g['tags']=sorted(set(g['tags']+['Recent platformer release or edition']))
   if collision:
    g['platformerInfo']['identityNote']='Shared stable ID with another genre; original source record and personal-library identity preserved.'
   games[ident]=g
 return games

def complete_platformer_metadata(catalog,root):
 root=pathlib.Path(root);sources=source_sets(root)
 dates=[catalog.get('generatedAt')]+[s.get('generatedAt') for s in sources]
 catalog['generatedAt']=max(d for d in dates if d) if any(dates) else None
 b=catalog['build'];rows=[g for g in catalog['items'] if HUB in g.get('hubs',[])]
 b['candidateUnresolved']=b.get('candidateUnresolved',[])+sources[0].get('unresolved',[])
 b['platformerResearch']={'records':len(rows),'steam':sum(bool(g.get('steamUrl')) for g in rows),'external':sum(not g.get('steamUrl') for g in rows),'individualEditorialNotes':sum(g['platformerInfo']['editorialDepth']=='Individual editorial note' for g in rows),'released':sum(g['status']=='Released' for g in rows),'earlyAccess':sum(g['status']=='Early Access' for g in rows),'upcoming':sum(bool(g.get('comingSoon')) for g in rows),'artwork':sum(bool(g.get('image')) for g in rows),'videos':sum(any(t.get(k) for k in ['mp4','webm','hls','youtube']) for g in rows for t in g.get('trailers',[])),'gemShortlist':sum(bool(g.get('hiddenGem')) for g in rows),'unresolvedCandidates':len(sources[0].get('unresolved',[]))}
 if rows:catalog['sources'].append({'provider':'Platformer study','kind':'editorial-research','description':'Curated platformers, clearly marked hybrids, console and creator releases. Primary-source facts and editorial fit remain distinct; coverage is not exhaustive.'})
 return catalog
