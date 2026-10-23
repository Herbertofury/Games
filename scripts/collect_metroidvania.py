#!/usr/bin/env python3
"""Incremental official facts for the Metroidvania hub; discovery is not recommendation."""
import argparse,concurrent.futures,datetime as dt,functools,hashlib,json,pathlib,re,unicodedata,urllib.parse
from bs4 import BeautifulSoup
import refresh,discover_storefronts as net
ROOT=pathlib.Path(__file__).resolve().parents[1]
HUB='Metroidvanias'
EXCLUDED={
'NoseBound':'Point-and-click adventure, not a Metroidvania.',
'There Is No Light':'Linear combat-focused action adventure; omitted to keep the exploration selection focused.',
'Nuclear Blaze':'Primarily linear firefighting platformer rather than ability-gated world exploration.',
'Shantae and the Seven Sirens Spectacular Superstar Update':'An update, not a separate game identity.',
'Doomed to Hell':'Arena roguelite, not a Metroidvania.',
'Sunblaze':'Level-based precision platformer, not a Metroidvania.',
'Mini Healer':'Boss-battle healer simulator, not a Metroidvania.',
'Gooma':'Ambiguous candidate; no recommendation promoted from the name alone.',
'Doomed Lands':'Survival crafting rather than a Metroidvania.',
'Touhou Artificial Dream in Arcadia':'First-person turn-based dungeon RPG, not a Metroidvania.',
'Alekon':'Photography adventure, not a Metroidvania.',
'Castle of Vania':'Ambiguous candidate; no exact edition promoted.',
'FlipWitch - Forbidden Sex Hex':'Explicit adult title excluded from this general-audience game collection.',
'Kunado Chronicles':'Visual novel, not a Metroidvania.',
'Mystery of Fortune':'Different RPG lineage, not a Metroidvania.',
'Plastomorphosis':'Survival horror rather than a Metroidvania.',
'Salt 2: Shores of Gold':'Open-world survival rather than a Metroidvania.',
'Sotano':'Puzzle escape game, not a Metroidvania.',
'Sparks of Hope':'Unresolved ambiguous title; not promoted as a Metroidvania.',
'The Tale of Onogoro':'VR puzzle adventure, not a Metroidvania.',
'The Witch\'s House MV':'MV is an engine/edition label here, not the Metroidvania genre.',
'Exorcist: Reviewer of Minds':'Ambiguous candidate; not promoted without an exact relevant identity.',
'Touhou: New World':'Action RPG without the requested central world-unlocking loop.',
'Blade & Bones':'Loose action-RPG neighbor; not promoted into this collection.',
'BLADE & BASTARD':'Unresolved genre/identity mismatch.',
'Altered Beast':'Arcade beat-em-up, not a Metroidvania.',
'Altheia: The Wrath of Aferi':'Loose adventure neighbor; omitted from the Metroidvania selection.',
'Anima: Song from the Abyss':'Loose action-RPG neighbor; not promoted.',
'Earthion':'Horizontal shoot-em-up, not a Metroidvania.',
'Earthblade':'Cancelled project; do not advertise as a playable recommendation.',
'Folly of the Wizards':'Roguelite rather than a persistent-world Metroidvania.',
'Forge of the Fae':'Turn-based RPG, not a Metroidvania.',
'Haplo':'Ambiguous discovery name; no exact genre identity promoted.',
'Hirogami':'Primarily linear 3D platformer, not a Metroidvania.',
'Project Anomaly: Urban Supernatural Investigator':'Different adventure format; not promoted.',
'Rogue Flight':'Rail shooter, not a Metroidvania.',
'The Witch of Fern Island':'Life/farming simulation, not a Metroidvania.',
'TrinityS':'Co-op boss-rush game, not a Metroidvania.',
'Whisper Mountain Outbreak':'Survival-horror co-op, not a Metroidvania.',
'Witchbrook':'Life simulation, not a Metroidvania.',
'Yes, Your Grace: Snowfall':'Kingdom-management game, not a Metroidvania.',
'Darksiders Genesis':'Level-based isometric action; excluded from the exploration-focused neighbors.',
'Doomsday Hunters':'Twin-stick roguelite, not a Metroidvania.',
'A Valley Without Wind 2':'Strategy/platform hybrid rather than the requested exploration loop.',
'RogueVania':'Ambiguous identity; not promoted by genre-sounding name alone.',
'Fury Unleashed':'Run-and-gun roguelite, not a Metroidvania.',
'Oblivion Eagle':'No exact relevant identity established.',
'Spiritfall':'Platform-fighter roguelite, not a Metroidvania.',
'30XX':'Level-based roguelite; excluded from persistent-world exploration.',
'20XX':'Level-based roguelite; excluded from persistent-world exploration.',
'Revita':'Room-based roguelite, not a Metroidvania.',
'Skul: The Hero Slayer':'Linear-run action roguelite, not a Metroidvania.',
'Have a Nice Death':'Run-based action roguelite, not a Metroidvania.',
'Zoria: Age of Shattering':'Tactical RPG, not a Metroidvania.',
'Ninja Five-O':'Level-based action platformer, not a Metroidvania.',
'Ninja Gaiden: Ragebound':'Level-based action platformer, not a Metroidvania.',
'Primal Light':'Linear action platformer; not promoted as a Metroidvania.',
'Castle of Heart':'Linear action platformer; not promoted as a Metroidvania.',
'Haydee':'Adult-styled adjacent puzzle shooter; omitted from the central genre selection.',
'Haydee 2':'Adult-styled adjacent puzzle shooter; omitted from the central genre selection.',
'Haydee 3':'Adult-styled adjacent puzzle shooter; omitted from the central genre selection.'}
ALIASES={'nineyearsofshadows':'9yearsofshadows','mobiusmachine':'themobiusmachine','awakenastralblade':'awakenastralblade','beyondtheicepalaceii':'beyondtheicepalace2','zau':'talesofkenzerazau','recordoflodosswardeedlitinwonderlabyrinth':'recordoflodosswardeedlitinwonderlabyrinth','akurra':'islesofseaandsky','doomedknight':'thedoomedknight'}
EXTERNAL_NAMES={'Super Metroid','Metroid Prime Remastered','Metroid Prime 4: Beyond','Shinsekai: Into the Depths','Shantae','Momodora II','Lyle in Cube Sector','Treasure Adventure Game'}
def norm(s):
 s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower().replace('&','and')
 return re.sub('[^a-z0-9]','',s)
def key(s):
 n=norm(s);return ALIASES.get(n,n)
def seeds():
 out={};duplicates=[];excluded=[];external=[];group='';fit=8;scope='Traditional Metroidvania'
 for line in (ROOT/'data/metroidvania-seeds.txt').read_text().splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  if line.startswith('['):group,fit,scope=line[1:-1].split('|');fit=int(fit);continue
  parts=line.split('|');name=parts[0];n=key(name)
  if name in EXCLUDED:excluded.append({'candidate':name,'state':'excluded','reason':EXCLUDED[name]});continue
  if name in EXTERNAL_NAMES:external.append({'candidate':name,'state':'external-route','reason':'Resolve through its exact creator or console distribution, not an unrelated Steam title.'});continue
  if n in out:duplicates.append({'candidate':name,'canonicalCandidate':out[n]['name']});continue
  out[n]={'name':name,'collection':group,'fit':int(parts[1]) if len(parts)>1 else fit,'scope':scope,'appid':int(parts[2]) if len(parts)>2 else None,'discoverySource':'Curated genre research'}
 more=ROOT/'data/metroidvania-additions.json'
 if more.exists():
  for x in json.loads(more.read_text()).get('steam',[]):out[key(x['name'])]=x
 return list(out.values()),duplicates,excluded,external
refresh.details=functools.lru_cache(maxsize=None)(refresh.details)
def resolve(seed,old,force):
 prior=next((g for g in old if key(g.get('seedName',g['name']))==key(seed['name']) or (seed.get('appid') and g.get('appid')==seed['appid'])),None)
 if prior and not force and prior.get('verifiedAt'):
  if (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior['verifiedAt'])).total_seconds()<86400:return prior
 try:
  aid=seed.get('appid');candidates=[]
  if not aid:
   search='https://store.steampowered.com/api/storesearch/?'+urllib.parse.urlencode({'term':seed['name'],'l':'english','cc':'us'})
   candidates=refresh.get(search).get('items',[])
   found=next((x for x in candidates if key(x['name'])==key(seed['name'])),None)
   if not found:raise ValueError('Exact identity needs reconciliation')
   aid=found['id']
  d=refresh.details(aid)
  if not d or d.get('type')!='game':raise ValueError('Official metadata did not confirm a game')
  allowed=[seed['name']]+seed.get('aliases',[])
  if not any(key(d['name'])==key(x) for x in allowed):raise ValueError('Explicit ID title mismatch: '+d['name'])
  g=refresh.resolve({'appid':aid,'name':d['name'],'fit':seed['fit'],'collection':seed['collection']},{},True)
  if g.get('verification')!='verified':raise ValueError(str(g.get('warnings')))
  group=seed['collection']
  if group=='Upcoming & playable demo watchlist':group='Fresh discoveries & emerging worlds'
  u=g['steamUrl'];about=refresh.text(d.get('about_the_game',''))
  g.update(seedName=seed['name'],hubs=[HUB],collections=[group],collection=group,primaryUrl=u,provider='Steam',kind='Standalone game',genreScope=seed['scope'],aliases=seed.get('aliases',[]))
  g['storefronts']=[{'provider':'Steam','url':u,'kind':'wishlist' if g['comingSoon'] else 'store','verified':True,'lastChecked':refresh.NOW}]
  g['demoAppids']=[x['appid'] for x in d.get('demos',[]) if x.get('appid')]
  g['metroidvaniaEvidence']={'sourceUrl':u,'description':about,'discoverySource':seed.get('discoverySource'),'genreClaim':bool(re.search(r'metroidvania|metroid.vania',about,re.I))}
  g['tags']=sorted(set(g['tags']+['Metroidvania collection',seed['scope']]+(['Demo available'] if g['demoAppids'] else [])))
  if g['comingSoon']:g['recommendationCaution']='Watchlist only: the full game is not released. A listed demo is a separate playable build.'
  if 'adjacent' in seed['scope'].lower() or 'hybrid' in seed['scope'].lower():g['recommendationCaution']='Explicitly labelled genre neighbor or hybrid, not a traditional persistent-world Metroidvania.'
  return g
 except Exception as e:
  if prior:return dict(prior,lastRefreshError=str(e))
  return {'candidate':seed['name'],'collection':seed['collection'],'error':str(e),'matches':[{'appid':x['id'],'name':x['name']} for x in locals().get('candidates',[])],'verification':'unresolved'}
def discovery_index():
 url='https://www.metroidvania.gg/2026'
 try:
  raw,final,_=net.read(url);s=BeautifulSoup(raw,'html.parser')
  rows=[]
  for a in s.select('a[href]'):
   ims=a.select('img');label=a.get_text(' ',strip=True) or ' '.join(i.get('alt','') for i in ims)
   href=urllib.parse.urljoin(final,a['href'])
   if label or '/app/' in href:rows.append({'label':label,'url':href,'images':[{'alt':i.get('alt'),'src':i.get('src')} for i in ims]})
  return {'url':final,'checkedAt':refresh.NOW,'links':rows,'embeddedData':[x.get_text() for x in s.select('script[type="application/json"],script#__NEXT_DATA__')]}
 except Exception as e:return {'url':url,'error':str(e)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--force',action='store_true');a=ap.parse_args()
 candidates,dupes,excluded,external=seeds();p=ROOT/'data/metroidvania-steam.json';old=json.loads(p.read_text()).get('items',[]) if p.exists() else []
 out=[];pending=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for result in pool.map(lambda x:resolve(x,old,a.force),candidates):
   print(result.get('verification'),result.get('name',result.get('candidate')),flush=True)
   (out if result.get('id') else pending).append(result)
 unique={}
 for g in out:
  if g['id'] in unique:
   prior=unique[g['id']];prior['aliases']=list(dict.fromkeys(prior.get('aliases',[])+[g['seedName']]));dupes.append({'candidate':g['seedName'],'canonicalCandidate':prior['name'],'id':g['id']})
  else:unique[g['id']]=g
 out=sorted(unique.values(),key=lambda x:x['name'].casefold())
 data={'schemaVersion':1,'generatedAt':refresh.NOW,'inputCount':len(candidates),'items':out,'unresolved':pending,'duplicates':dupes,'dispositions':excluded+external}
 data['datasetHash']=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'data/metroidvania-discovery-index.json').write_text(json.dumps(discovery_index(),ensure_ascii=False,indent=2)+'\n')
 report={'inputs':len(candidates),'resolved':len(out),'excluded':len(excluded),'duplicates':len(dupes),'externalRoutes':external,'missingVideo':[{'id':g['id'],'name':g['name']} for g in out if not any(any(t.get(k) for k in ('hls','mp4','webm','youtube')) for t in g.get('trailers',[]))],'unresolved':pending}
 (ROOT/'data/metroidvania-discovery-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
