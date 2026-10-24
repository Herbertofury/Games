"""Two survival hubs sharing one catalog and one persistent identity per game."""
import copy,datetime as dt,json,urllib.parse
HUBS=('Survival','Minecraft-like worlds')
def load(root,name,default):
 p=root/'data'/name;return json.loads(p.read_text()) if p.exists() else default

def integrate(root,games):
 from source_links import normalized_links
 for ident,previous in list(games.items()):
  if previous.get("hubs") and set(previous["hubs"])<=set(HUBS):del games[ident]
  elif any(h in HUBS for h in previous.get("hubs",[])):previous["hubs"]=[h for h in previous["hubs"] if h not in HUBS]
 steam=load(root,'survival-steam.json',{'items':[]});external=load(root,'survival-external.json',{'items':[]});overrides={}
 for filename in ['survival-storefronts.json','survival-curation.json','survival-media.json','survival-chronology.json','survival-verified-stores.json']:
  for ident,row in load(root,filename,{'overrides':{}}).get('overrides',{}).items():
   dest=overrides.setdefault(ident,{})
   for k,v in row.items():
    if k in ['sources','storefronts','trailers','tags']:dest[k]=dest.get(k,[])+copy.deepcopy(v)
    elif k=='_replace':dest.setdefault(k,{}).update(copy.deepcopy(v))
    else:dest[k]=copy.deepcopy(v)
 ids=[];excluded=[]
 for raw in steam['items']+external['items']:
  ident=raw['id'];extra=overrides.get(ident,{})
  if extra.get('excludeFromPublication'):
   excluded.append({'candidate':raw['name'],'id':ident,'state':'not-promoted','reason':extra.get('publicationReason','Source review required')});continue
  g=copy.deepcopy(raw)
  for k,v in extra.items():
   if k not in ['sources','storefronts','trailers','tags','_replace']:g[k]=copy.deepcopy(v)
  for k,v in extra.get('_replace',{}).items():g[k]=copy.deepcopy(v)
  for k in ['sources','storefronts','trailers']:
   def identity(x):return x.get('url') or x.get('youtube') or x.get('vimeo') or x.get('hls') or x.get('mp4') or x.get('webm') or x.get('sourceUrl')
   g[k]=list({identity(x):x for x in g.get(k,[])+extra.get(k,[])}.values())
  g['tags']=sorted(set(g.get('tags',[])+extra.get('tags',[]))-{'Recent survival release'})
  hub=next(h for h in g['hubs'] if h in HUBS);scope=g.get('genreScope','Survival crafting');collection=g['collection']
  g['survivalHub']=hub;g['survivalCollection']=collection;g['survivalFit']=g.get('fit');g['survivalScope']=scope;g['survivalWhy']=g.get('curatorWhy') or g['summary']
  core=not any(word in scope.lower() for word in ['adjacent','colony','automation sandbox','experimental','turn-based','voxel action rpg'])
  tags=['Survival core' if core else 'Survival neighbor']
  if hub==HUBS[1]:tags+=['Minecraft-like collection']
  if '2d' in scope.lower() or 'Terraria-like' in collection:tags.append('Terraria-like worlds')
  if any(w in scope.lower() for w in ['voxel survival','block','brick']):tags.append('Block-building survival')
  if 'Co-op' in g.get('tags',[]) or any('co-op' in x.lower() for x in g.get('features',[])):tags.append('Co-op')
  if 'Single-player' in g.get('features',[]):tags.append('Single-player listed')
  date=g.get('releaseDate')
  if date and date[:4].isdigit() and date[:4]>='2025' and not g.get('comingSoon') and (g.get('originalReleaseYear') or int(date[:4]))>=2025:tags.append('Recent survival release')
  if not g.get('steamUrl'):tags.append('Creator-hosted world')
  if collection in ['Shared-world adventures','Oceans, pirates & floating homes','Tribes, settlements & historical frontiers'] and core:tags.append('Conan / ARK / Windrose feeling')
  g['tags']=sorted(set(g['tags']+tags));ev=g.get('survivalEvidence',{})
  single='Listed by Steam' if ev.get('singlePlayerListed') else 'Check the exact creator or store edition'
  coop='Co-op is listed by the store' if ev.get('coopListed') else 'Not confirmed by the source feature list'
  g['survivalInfo']={'world':scope,'solo':single,'coop':coop,'hosting':'Dedicated servers mentioned in the official description' if ev.get('dedicatedServerMentioned') else 'Dedicated-server support not independently confirmed','modding':'Mods or workshop mentioned by the source' if ev.get('moddingMentioned') else 'Check the creator documentation; not inferred from genre','terrain':'Terrain / voxel systems mentioned by the source' if ev.get('terrainMentioned') else 'See gameplay for terrain-editing and construction limits','basis':ev.get('basis','Source-grounded genre selection. Server, offline and cross-play compatibility must be checked for the exact edition.'),'sourceUrl':ev.get('sourceUrl') or g['primaryUrl']}
  if g.get('survivalInfoOverride'):g['survivalInfo'].update(g.pop('survivalInfoOverride'))
  g['storefronts']=normalized_links(g.get('storefronts',[]))
  # News/media citations belong in Sources, not masquerading as shops or downloads.
  nonstores=[x for x in g['storefronts'] if x.get('kind') in ['news','media','engine','source']]
  g['sources']=list({x['url']:x for x in g.get('sources',[])+nonstores}.values());g['storefronts']=[x for x in g['storefronts'] if x.get('kind') not in ['news','media','engine','source']]
  for s in g['storefronts']:s.pop('editionEvidence',None)
  for aid in g.get('demoAppids',[]):
   u=f'https://store.steampowered.com/app/{aid}/'
   if not any(x['url'].rstrip('/')==u.rstrip('/') for x in g['storefronts']):g['storefronts'].append({'provider':'Steam','url':u,'kind':'demo','verified':True,'lastChecked':g.get('verifiedAt'),'sourceUrl':g['steamUrl'],'editionNote':'Demo edition explicitly linked by the official Steam metadata.'})
  for k in ['mediaEvidence','videoCandidates','creatorEvidence','survivalSourceVersion']:g.pop(k,None)
  g.setdefault('appid',None);g.setdefault('collections',[collection]);g.setdefault('primaryUrl',g.get('steamUrl'));g.setdefault('provider','Steam' if g.get('steamUrl') else 'Official site');g.setdefault('kind','Standalone game');g.setdefault('developers',[]);g.setdefault('warnings',[])
  # A game already in another genre keeps that genre's identity, artwork and rating lineage.
  if ident in games and any(h not in HUBS for h in games[ident].get('hubs',[])):
   old=games[ident];old['hubs']=list(dict.fromkeys(old['hubs']+g['hubs']));old['collections']=list(dict.fromkeys(old.get('collections',[old['collection']])+g['collections']));old['tags']=sorted((set(old.get('tags',[]))-{'Recent survival release'})|set(g['tags']))
   for field in ['survivalHub','survivalCollection','survivalFit','survivalScope','survivalWhy','survivalInfo']:old[field]=copy.deepcopy(g[field])
   for field in ['earlyAccessReleaseDate','releaseChronology']:
    if g.get(field):old[field]=copy.deepcopy(g[field])
   if g.get('originalReleaseYear'):old['originalReleaseYear']=min(old.get('originalReleaseYear') or g['originalReleaseYear'],g['originalReleaseYear'])
   old['storefronts']=normalized_links(old.get('storefronts',[])+g['storefronts']);old['sources']=list({x['url']:x for x in old.get('sources',[])+g['sources']}.values())
  else:games[ident]=g
  ids.append(ident)
 dates=[x.get('generatedAt') for x in [steam,external,load(root,'survival-chronology.json',{})] if x.get('generatedAt')];review=load(root,'survival-reconciliation.json',{})
 names={g['id']:g['name'] for g in steam['items']+external['items']}
 dispositions=copy.deepcopy(review.get('dispositions',steam.get('dispositions',[])+external.get('dispositions',[]))+excluded)
 for record in dispositions:
  record.setdefault('candidate',names.get(record.get('id'),record.get('id') or 'Unresolved discovery'))
 return {'ids':sorted(set(ids)),'generatedAt':max(dates) if dates else None,'unresolved':review.get('unresolved',steam.get('unresolved',[])),'dispositions':dispositions}
