"""Source-preserving, mode-aware couch multiplayer overlay."""
import copy, json, re
HUB='Couch co-op & party'
SOURCE_FILES=['party-steam.json','party-extra.json','party-recovered.json','party-external.json']
def load(root,name,default):
 p=root/'data'/name
 return json.loads(p.read_text()) if p.exists() else default

def integrate(root,games):
 from source_links import normalized_links
 # Rebuild this overlay only; other genre memberships and stable IDs survive.
 for ident,g in list(games.items()):
  if g.get('hubs')==[HUB]:del games[ident]
  elif HUB in g.get('hubs',[]):g['hubs']=[h for h in g['hubs'] if h!=HUB]
 sources=[load(root,n,{'items':[]}) for n in SOURCE_FILES];raw={};overrides={}
 for source in sources:
  for g in source['items']:raw[g['id']]=copy.deepcopy(g)
 for n in ['party-storefronts.json','party-extra-stores.json','party-recovered-stores.json','party-media.json','party-curation.json']:
  for ident,extra in load(root,n,{'overrides':{}}).get('overrides',{}).items():
   dest=overrides.setdefault(ident,{})
   for k,v in extra.items():
    if k in ['storefronts','sources','trailers','tags']:dest[k]=dest.get(k,[])+copy.deepcopy(v)
    elif k=='_replace':dest.setdefault(k,{}).update(copy.deepcopy(v))
    else:dest[k]=copy.deepcopy(v)
 published=[];dispositions=[]
 for ident,g in raw.items():
  ov=overrides.get(ident,{})
  if ov.get('excludeFromPublication'):
   dispositions.append({'candidate':g['name'],'id':ident,'state':'not-promoted','reason':ov['publicationReason']});continue
  for k,v in ov.items():
   if k not in ['storefronts','sources','trailers','tags','_replace']:g[k]=copy.deepcopy(v)
  for k,v in ov.get('_replace',{}).items():g[k]=copy.deepcopy(v)
  for k in ['storefronts','sources','trailers']:
   def identity(x):return x.get('url') or x.get('youtube') or x.get('vimeo') or x.get('hls') or x.get('mp4') or x.get('webm') or x.get('sourceUrl')
   g[k]=list({identity(x):x for x in g.get(k,[])+ov.get(k,[])}.values())
  g['storefronts']=normalized_links(g.get('storefronts',[]))
  for s in g['storefronts']:s.pop('descriptionEvidence',None)
  g['sources']=list({s['url']:s for s in g.get('sources',[])+[s for s in g['storefronts'] if s.get('kind') in ['news','media','source','engine']]}.values())
  g['storefronts']=[s for s in g['storefronts'] if s.get('kind') not in ['news','media','source','engine']]
  p=g['partyInfo'];modes=p.get('modesDetail',[])
  counts=sorted({n for m in modes for n in m.get('counts',[]) if isinstance(n,int) and n>=2})
  p.update(playerCounts=counts,localMax=max(counts) if counts else None,countVerified=bool(counts),modes=sorted({m['type'] for m in modes}))
  p['coopCounts']=sorted({n for m in modes if m['type']=='Co-op' for n in m.get('counts',[])})
  p['versusCounts']=sorted({n for m in modes if m['type']=='Versus' for n in m.get('counts',[])})
  p['basis']='Local capacities are edition- and mode-specific. Team-versus is not a cooperative campaign. Online players, bots, spectators and tournament brackets are not simultaneous couch players. Optional DLC and controller conditions stay visible.'
  p.pop('countCandidates',None);p.pop('countHint',None);p.pop('modeHint',None)
  g['partyCollection']=g.get('partyCollection',g['collection']);g['partyFit']=g.get('partyFit',g.get('fit'));g['partyWhy']=g.get('partyWhy') or g.get('curatorWhy') or g['summary'];g['partyScope']='Local multiplayer / '+('co-op and versus' if len(p['modes'])>1 else '/'.join(p['modes']).lower())
  tags=set(g.get('tags',[])+ov.get('tags',[]));tags.add('Couch multiplayer')
  for n in counts:tags.add(f'{n} local players')
  if p['coopCounts']:tags.add('Local co-op')
  if p['versusCounts']:tags.add('Local versus')
  if g.get('knownFavorite'):tags.add('Your reference favorite')
  if g['partyCollection']=='Your favorites & closest matches':tags.add('Disc Jam / Lethal League feeling')
  if p.get('participation')=='phones':tags.add('Phone controllers')
  if p.get('participation')=='hotseat':tags.add('Pass-the-pad / hotseat')
  if p.get('participation')=='asymmetric':tags.add('VR / asymmetric setup')
  if 'Nintendo' in p.get('platform','') or 'Switch' in p.get('platform',''):tags.add('Console edition')
  date=g.get('releaseDate');history=g.get('earlyAccessReleaseDate')
  original=g.get('originalReleaseYear') or (int(history[:4]) if history and history[:4].isdigit() else None)
  if date and date[:4].isdigit() and date[:4]>='2025' and not g.get('comingSoon') and (original or int(date[:4]))>=2025:tags.add('Recent couch release')
  if original:g['originalReleaseYear']=original
  g['tags']=sorted(tags);g.setdefault('appid',None);g.setdefault('developers',[]);g.setdefault('features',[]);g.setdefault('warnings',[]);g.setdefault('genres',[]);g.setdefault('kind','Standalone game');g.setdefault('primaryUrl',g.get('steamUrl'));g.setdefault('collections',[g['partyCollection']]);g['hubs']=[HUB]
  for aid in g.get('demoAppids',[]):
   url=f'https://store.steampowered.com/app/{aid}/'
   if not any(s['url'].rstrip('/')==url.rstrip('/') for s in g['storefronts']):g['storefronts'].append({'provider':'Steam','url':url,'kind':'demo','verified':True,'lastChecked':g.get('verifiedAt'),'sourceUrl':g['steamUrl'],'editionNote':'Separate demo linked by the official Steam metadata. Demo modes may differ from the full game.'})
  for k in ['partyEvidence','mediaEvidence','creatorEvidence','videoCandidates','rawDescription']:g.pop(k,None)
  if ident in games:
   old=games[ident];old['hubs']=list(dict.fromkeys(old.get('hubs',[])+[HUB]));old['collections']=list(dict.fromkeys(old.get('collections',[old['collection']])+g['collections']));old['tags']=sorted(set(old.get('tags',[])+g['tags']))
   for field in ['partyCollection','partyFit','partyWhy','partyInfo','partyScope','knownFavorite']:
    if field in g:old[field]=copy.deepcopy(g[field])
   old['storefronts']=normalized_links(old.get('storefronts',[])+g['storefronts']);old['sources']=list({s['url']:s for s in old.get('sources',[])+g['sources']}.values())
  else:games[ident]=g
  # Some Steam movie records are posters without a playable stream. Keep their
  # provenance, but never render them as empty first-choice video players.
  published_game=games[ident]
  unsupported=[t for t in published_game.get('trailers',[]) if not any(t.get(k) for k in ['hls','mp4','webm','youtube','vimeo'])]
  if unsupported:
   archived=published_game.get('unavailableVideoMetadata',[])+unsupported
   published_game['unavailableVideoMetadata']=list({json.dumps(t,sort_keys=True):t for t in archived}.values())
   published_game['trailers']=[t for t in published_game['trailers'] if t not in unsupported]
  published.append(ident)
 report=load(root,'party-reconciliation.json',{})
 for row in report.get('dispositions',[]):
  row.setdefault('candidate',row.get('name') or row.get('requestedName') or row.get('id'))
  row.setdefault('state','unresolved-active')
 for row in report.get('unresolved',[]):
  row.setdefault('candidate',row.get('name') or row.get('requestedName') or row.get('id'))
  row.setdefault('state','unresolved-active')
 dates=[s.get('generatedAt') for s in sources if s.get('generatedAt')]+[load(root,'party-curation.json',{}).get('generatedAt')]
 return {'ids':sorted(published),'generatedAt':max([x for x in dates if x],default=None),'dispositions':dispositions+report.get('dispositions',[]),'unresolved':report.get('unresolved',[])}
