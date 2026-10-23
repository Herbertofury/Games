"""Deterministic Metroidvania overlay; other genre identities remain authoritative."""
import copy,json,re
HUB='Metroidvanias'
ADJACENT={
 'Owlboy':'Narrative platform adventure / Metroidvania-adjacent',
 'Gal Guardians: Demon Purge':'Stage-based action / Metroidvania-adjacent',
 'Shantae: Half-Genie Hero Ultimate Edition':'Stage-based exploration / Metroidvania-adjacent',
 'Super Zangyura':'Stage-based exploration / Metroidvania-adjacent',
 'Odallus: The Dark Call':'Stage-based exploration / Metroidvania-adjacent',
 'Watcher Chronicles':'Soulslike action / Metroidvania-adjacent',
 'The Swapper':'Puzzle / knowledge exploration',
 "A Monster's Expedition":'Puzzle / knowledge exploration',
 'ElecHead':'Puzzle / knowledge exploration',
 'Foregone':'Stage-based action / Metroidvania-adjacent',
 'Oblivion Override':'Roguelite / Metroidvania hybrid',
 'Crypt Custodian':'Top-down Metroidvania','Pseudoregalia':'3D Metroidvania',
 'Frogmonster':'3D Metroidvania','Vomitoreum':'3D Metroidvania',
 'Supraland':'3D Metroidvania','Supraland Six Inches Under':'3D Metroidvania',
 'Supraworld':'3D Metroidvania','Maseylia : Echoes of the Past':'3D Metroidvania',
 'Maseylia: Echoes of the Past':'3D Metroidvania',
 'Knytt Classic':'Atmospheric exploration / Metroidvania-adjacent',
 'Rain World':'Survival exploration / Metroidvania-adjacent'
}
def read(root,name,default):
 p=root/'data'/name;return json.loads(p.read_text()) if p.exists() else default

def integrate(root,games):
 from source_links import normalized_links
 sources=[read(root,'metroidvania-steam.json',{'items':[]}),read(root,'metroidvania-external.json',{'items':[]})]
 overrides={}
 for name in ['metroidvania-storefronts.json','metroidvania-curation.json','metroidvania-media.json']:
  for ident,extra in read(root,name,{'overrides':{}}).get('overrides',{}).items():
   row=overrides.setdefault(ident,{})
   for k,v in extra.items():
    if k in ['storefronts','sources','trailers','tags']:row[k]=row.get(k,[])+copy.deepcopy(v)
    elif k=='_replace':row.setdefault(k,{}).update(copy.deepcopy(v))
    else:row[k]=copy.deepcopy(v)
 accepted={g['id'] for s in sources for g in s['items'] if not overrides.get(g['id'],{}).get('excludeFromPublication')}
 # An updated source slice can remove stale MV-only rows, never another genre's entry.
 for ident in list(games):
  if games[ident].get('hubs')==[HUB] and ident not in accepted:del games[ident]
 published=[]
 for src in sources:
  for raw in src['items']:
   ident=raw['id'];extra=overrides.get(ident,{})
   if ident not in accepted:continue
   g=copy.deepcopy(raw);g.update({k:v for k,v in extra.items() if k not in ['storefronts','sources','trailers','tags','_replace']})
   for k in ['storefronts','sources','trailers','tags']:
    if k=='tags':g[k]=sorted(set(g.get(k,[])+extra.get(k,[])));continue
    def identity(x):return x.get('url') or x.get('youtube') or x.get('vimeo') or x.get('hls') or x.get('mp4') or x.get('webm') or x.get('sourceUrl')
    g[k]=list({identity(x):x for x in g.get(k,[])+extra.get(k,[])}.values())
   # Explicit replacements have final precedence over stale scraped media/editions.
   for k,v in extra.get('_replace',{}).items():g[k]=copy.deepcopy(v)
   g['storefronts']=normalized_links(g.get('storefronts',[]));g.setdefault('hubs',[HUB]);g.setdefault('collections',[g['collection']]);g.setdefault('primaryUrl',g.get('steamUrl'));g.setdefault('provider','Steam' if g.get('steamUrl') else 'Official site');g.setdefault('kind','Standalone game');g.setdefault('appid',None)
   scope=extra.get('genreScope') or ADJACENT.get(g['name']) or g.get('genreScope') or 'Traditional Metroidvania';g['genreScope']=scope
   core=not any(x in scope.lower() for x in ['adjacent','hybrid','stage-based','knowledge'])
   genre_tags={'MV core','MV adjacent / hybrid','MV 3D','MV puzzle-led','MV dark fantasy','Recent Metroidvania release'}
   g['tags']=sorted(set(t for t in g.get('tags',[]) if t not in genre_tags)|{HUB,'MV core' if core else 'MV adjacent / hybrid'})
   if '3d' in scope.lower() or 'first-person' in scope.lower() or '3D & first-person' in g['collection']:g['tags'].append('MV 3D')
   if any(x in (g['collection']+' '+scope).lower() for x in ['puzzle','knowledge']):g['tags'].append('MV puzzle-led')
   if any(x in g['collection'].lower() for x in ['dark fantasy','soulslike','retro castles']):g['tags'].append('MV dark fantasy')
   date=g.get('releaseDate')
   if date and date>='2025-01-01' and not g.get('comingSoon') and (g.get('originalReleaseYear') or int(date[:4]))>=2025:g['tags'].append('Recent Metroidvania release')
   if g.get('comingSoon'):
    g['watchlistInterest']=g.get('fit');g['fit']=None
    g['recommendationCaution']='Unreleased watchlist entry. Interest level is not a scored recommendation or a completed review. Any demo is a separate build.'
   g['tags']=sorted(set(g['tags']));ev=g.get('metroidvaniaEvidence',{});about=ev.get('description') or g.get('summary','');mechanics=[]
   for pattern,label in [(r'double.jump','Double jump'),(r'wall.jump|wall.climb','Wall traversal'),(r'grappl|grapple','Grappling'),(r'\bdash','Dash movement'),(r'transform|shape.shift','Transformation'),(r'underwater|swim','Underwater traversal'),(r'\bparry|parries','Parry combat'),(r'time.loop|time.manipulat','Time mechanics')]:
    if re.search(pattern,about,re.I):mechanics.append(label)
   g['metroidvaniaInfo']={'structure':scope,'traversal':', '.join(mechanics) if mechanics else 'Explore the official gameplay and description for its progression systems.','basis':'Mechanics above are mentions in the source description, not an exhaustive ability inventory. Genre boundaries are editorial and adjacent formats are labelled.','sourceUrl':ev.get('sourceUrl') or g['primaryUrl']}
   if ev:g['metroidvaniaEvidence']={k:v for k,v in ev.items() if k!='description'};g['metroidvaniaEvidence']['descriptionExcerpt']=about[:700]
   for link in g['storefronts']:link.pop('descriptionEvidence',None)
   g.pop('mediaEvidence',None);g.pop('creatorEvidence',None)
   for aid in g.get('demoAppids',[]):
    u=f'https://store.steampowered.com/app/{aid}'
    if not any(x['url'].rstrip('/')==u for x in g['storefronts']):g['storefronts'].append({'provider':'Steam','url':u,'kind':'demo','verified':True,'lastChecked':g.get('verifiedAt'),'sourceUrl':g['steamUrl'],'editionNote':'Demo app explicitly linked by the official Steam metadata.'})
   if ident in games and any(h!=HUB for h in games[ident].get('hubs',[])):
    old=games[ident];old['hubs']=list(dict.fromkeys(old.get('hubs',[])+[HUB]));old['metroidvaniaInfo']=g['metroidvaniaInfo'];old['metroidvaniaFit']=g.get('fit');old['metroidvaniaCollection']=g['collection'];old['collections']=list(dict.fromkeys(old.get('collections',[])+g['collections']));old['tags']=sorted(set(old.get('tags',[])+g['tags']))
   else:games[ident]=g
   published.append(ident)
 dates=[s.get('generatedAt') for s in sources if s.get('generatedAt')];rec=read(root,'metroidvania-reconciliation.json',{})
 return {'ids':sorted(set(published)),'generatedAt':max(dates) if dates else None,'unresolved':sum([s.get('unresolved',[]) for s in sources],[]),'dispositions':rec.get('dispositions',[])}
