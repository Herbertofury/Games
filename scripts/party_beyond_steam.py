#!/usr/bin/env python3
"""Public creator and console source metadata; never infer a PC port or local capacity."""
import concurrent.futures,copy,datetime as dt,hashlib,html,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
import discover_storefronts as net,collect_external_media as media
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat();HUB='Couch co-op & party'
# Counts below are discovery targets. Publication requires a separately reviewed source excerpt.
SEEDS=[
('puff-puff-push','Puff Puff Push','https://typimals.itch.io/puff-puff-push',8,'Versus','simultaneous','PC edition',9),
('mutiny-bomb','MUTINY! Local Multiplayer Bomb Game','https://zsfer.itch.io/mutiny',10,'Versus','simultaneous','PC edition',8),
('duck-cover-2','Duck and Cover 2','https://siddikinz.itch.io/duck-and-cover-2',4,'Co-op,Versus','simultaneous','PC edition',9),
('pshnggg','PSHNGGG!','https://mint.itch.io/pshnggg',2,'Versus','simultaneous','PC edition',8),
('square-off-shiba','Square Off','https://shibadogstudios.itch.io/square-off',4,'Versus','simultaneous','PC edition',8),
('duck-and-gun','Duck and Gun','https://chelbling.itch.io/duck-and-gun',4,'Versus','simultaneous','PC edition',8),
('underhanded-combat','Underhanded Combat','https://nathanjoy.itch.io/underhanded-combat',2,'Versus','simultaneous','PC edition',8),
('sumaburu','Sumaburu','https://jakey-mg.itch.io/sumaburu',2,'Versus','simultaneous','PC edition',8),
('sumo-dumo','Sumo Dumo','https://sparacios.itch.io/sumo-dumo',2,'Versus','simultaneous','PC edition',8),
('supertuxkart','SuperTuxKart','https://supertuxkart.net/Main_Page',4,'Versus','simultaneous','PC edition',9),
('mario-kart-world','Mario Kart World','https://www.nintendo.com/us/store/products/mario-kart-world-switch-2/',4,'Versus','simultaneous','Nintendo Switch 2',10),
('mario-party-jamboree','Super Mario Party Jamboree','https://www.nintendo.com/us/store/products/super-mario-party-jamboree-switch/',4,'Versus','simultaneous','Nintendo Switch',10),
('mario-party-superstars','Mario Party Superstars','https://www.nintendo.com/us/store/products/mario-party-superstars-switch/',4,'Versus','simultaneous','Nintendo Switch',10),
('mario-kart-8-deluxe','Mario Kart 8 Deluxe','https://www.nintendo.com/us/store/products/mario-kart-8-deluxe-switch/',4,'Versus','simultaneous','Nintendo Switch',10),
('kirby-air-riders','Kirby Air Riders','https://www.nintendo.com/us/store/products/kirby-air-riders-switch-2/',4,'Versus','simultaneous','Nintendo Switch 2',9),
('smash-ultimate','Super Smash Bros. Ultimate','https://www.nintendo.com/us/store/products/super-smash-bros-ultimate-switch/',8,'Versus','simultaneous','Nintendo Switch',10),
('super-mario-bros-wonder','Super Mario Bros. Wonder','https://www.nintendo.com/us/store/products/super-mario-bros-wonder-switch/',4,'Co-op','simultaneous','Nintendo Switch',10),
('super-mario-3d-world-bowsers-fury','Super Mario 3D World + Bowser\'s Fury','https://www.nintendo.com/us/store/products/super-mario-3d-world-plus-bowsers-fury-switch/',4,'Co-op','simultaneous','Nintendo Switch',10),
('kirby-return-dreamland-deluxe','Kirby\'s Return to Dream Land Deluxe','https://www.nintendo.com/us/store/products/kirbys-return-to-dream-land-deluxe-switch/',4,'Co-op','simultaneous','Nintendo Switch',9),
('kirby-forgotten-land','Kirby and the Forgotten Land - Switch 2 Edition + Star-Crossed World','https://www.nintendo.com/us/store/products/kirby-and-the-forgotten-land-nintendo-switch-2-edition-plus-star-crossed-world-switch-2/',2,'Co-op','simultaneous','Nintendo Switch 2',9),
('snipperclips','Snipperclips - Cut it out, together!','https://www.nintendo.com/us/store/products/snipperclips-cut-it-out-together-switch/',4,'Co-op,Versus','simultaneous','Nintendo Switch',9),
('switch-sports','Nintendo Switch Sports','https://www.nintendo.com/us/store/products/nintendo-switch-sports-switch/',4,'Versus','simultaneous','Nintendo Switch',9),
('orbitals','Orbitals','https://www.nintendo.com/us/store/products/orbitals-switch-2/',2,'Co-op','simultaneous','Nintendo Switch 2',10)
]
CREATOR_LINKS={
'Wand Wars':'https://moonradish.itch.io/wand-wars',
'Push Me Pull You':'https://househouse.itch.io/push-me-pull-you',
'Jumpala':'https://yokereba.itch.io/jumpala',
'Rocket League':'https://store.epicgames.com/en-US/p/rocket-league'
}
def save(name,data):(R/'data'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def provider(url):
 h=urllib.parse.urlsplit(url).hostname or ''
 return 'Nintendo' if h.endswith('nintendo.com') else net.provider(url) or 'Official site'
def scrape(url):
 raw,final,_=net.read(url);s=BeautifulSoup(raw,'html.parser');p=media.parse(raw,final)
 for n in list(s.select('#comments,.comments,.comment_list,.community_posts,.post_grid,footer,nav')):n.decompose()
 main=s.select_one('.formatted_description') or s.select_one('article') or s;body=html.unescape(str(main).replace('\\/','/'))
 p['youtube']=list(dict.fromkeys(p.get('youtube',[])+re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',body)))
 files=[]
 for v in s.select('video,video source'):
  u=urllib.parse.urljoin(final,v.get('src',''))
  if v.get('src') and re.search(r'\.(?:mp4|webm|m3u8)(?:\?|$)',u):files.append(u)
 if 'nintendo.com' in final:
  files+=re.findall(r'https://assets\.nintendo\.com/video/[^\s\"\'<>]+\.(?:mp4|webm|m3u8)(?:\?[^\s\"\'<>]*)?',body)
 p.update(files=list(dict.fromkeys(files)),sourceUrl=final,description=main.get_text(' ',strip=True),hash=hashlib.sha256(raw.encode()).hexdigest(),outbound=[])
 p['metadata']=s.select_one('.game_info_panel_widget').get_text(' ',strip=True) if s.select_one('.game_info_panel_widget') else ''
 for a in main.select('a[href]'):
  u=urllib.parse.urljoin(final,a['href']);h=urllib.parse.urlsplit(u).hostname or ''
  if net.safe(u) and any(h==d or h.endswith('.'+d) for d in ['store.steampowered.com','gog.com','itch.io','patreon.com','store.epicgames.com','gamejolt.com','newgrounds.com']):p['outbound'].append({'url':u,'label':a.get_text(' ',strip=True)})
 p['jsonld']=[]
 for n in s.select('script[type="application/ld+json"]'):
  try:p['jsonld'].append(json.loads(n.get_text()))
  except ValueError:pass
 return p

def main():
 existing={g['id']:g for g in json.loads((R/'data/catalog.json').read_text())['items']};path=R/'data/party-external.json';old={g['id']:g for g in json.loads(path.read_text()).get('items',[])} if path.exists() else {};evidence={};errors=[];items=[]
 def one(seed):
  slug,name,url,cap,modes,part,platform,fit=seed;ident='external:'+slug
  try:
   p=scrape(url);g=copy.deepcopy(old.get(ident) or existing.get(ident) or {});g.update(id=ident,name=name,seedName=name,primaryUrl=p['sourceUrl'],provider=provider(url),collection='Console party essentials' if platform!='PC edition' else 'Free & creator-hosted party gems',partyFit=fit,fit=fit,hubs=[HUB],genres=['Action','Party'],features=[],tags=['Local multiplayer'],verification='verified',verifiedAt=NOW)
   g['partyCollection']=g['collection'];g['collections']=[g['collection']];g.setdefault('appid',None);g.setdefault('kind','Console game' if platform!='PC edition' else 'Standalone game');g.setdefault('status','Prototype' if 'In development' in p['metadata'] else 'Released');g.setdefault('comingSoon',False);g.setdefault('free',False);g.setdefault('rating',None);g.setdefault('reviewCount',0);g.setdefault('releaseDate',None);g.setdefault('releaseLabel','See creator / console release');g.setdefault('developers',[]);g.setdefault('platforms',[platform]);g.setdefault('summary',p.get('description','')[:500]);g.setdefault('screenshots',[]);g.setdefault('trailers',[])
   if '.itch.io' in url:g['free']=bool('Name your own price' in p['description'] or 'Download Now' in p['description'])
   if not g.get('image'):g['image']=p.get('image') or (p['pictures'][0] if p['pictures'] else None)
   g['screenshots']+= [{'src':u,'thumbnail':u,'alt':name+' creator screenshot','sourceUrl':p['sourceUrl'],'credit':'Creator / '+provider(url),'verified':True} for u in p.get('pictures',[]) if u!=g.get('image')]
   g['screenshots']=list({s['src']:s for s in g['screenshots']}.values())
   if not g['trailers']:
    for v in p['youtube']:g['trailers'].append({'youtube':v,'name':'Creator / publisher video','sourceUrl':p['sourceUrl'],'watchUrl':'https://www.youtube.com/watch?v='+v,'poster':g.get('image')})
    for v in p['files']:g['trailers'].append({('hls' if '.m3u8' in v else 'mp4' if '.mp4' in v else 'webm'):v,'name':'Publisher gameplay video','sourceUrl':p['sourceUrl'],'poster':g.get('image')})
   g.setdefault('storefronts',[]);g['storefronts'].append({'url':p['sourceUrl'],'provider':provider(url),'kind':'store' if platform!='PC edition' else 'project','verified':True,'lastChecked':NOW});g['storefronts']=list({x['url']:x for x in g['storefronts']}.values());g.setdefault('sources',[]);g['sources'].append({'url':p['sourceUrl'],'provider':provider(url),'verified':True,'lastChecked':NOW})
   g['partyInfo']={'countHint':cap,'countVerified':False,'localMax':None,'playerCounts':[],'modes':modes.split(','),'modesDetail':[],'participation':part,'platform':platform,'sourceUrl':p['sourceUrl'],'checkedAt':NOW,'inputs':'Read the game-specific controller requirements.','screen':'Shared / split screen; mode dependent','requiresInternet':'Not inferred from a local multiplayer listing.','evidence':[],'notes':'Exact platform and mode limits require source review.'}
   return g,p,None
  except Exception as error:return None,None,{'candidate':name,'id':ident,'sourceUrl':url,'state':'unresolved-active','reason':str(error)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for g,p,error in pool.map(one,SEEDS):
   if error:errors.append(error);print(error,flush=True)
   else:items.append(g);evidence[g['id']]=p;print(g['name'],len(g['trailers']),flush=True)
 creator={}
 for name,url in CREATOR_LINKS.items():
  try:creator[name]=scrape(url)
  except Exception as error:creator[name]={'url':url,'error':str(error)}
 save('party-external.json',{'schemaVersion':1,'generatedAt':NOW,'items':items,'dispositions':errors});save('party-external-evidence.json',{'generatedAt':NOW,'records':evidence,'creatorLinks':creator})
 print(json.dumps({'records':len(items),'unresolved':errors,'missingMedia':[g['id'] for g in items if not g.get('image') or not g.get('trailers')]},indent=2))
if __name__=='__main__':main()
