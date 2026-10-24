#!/usr/bin/env python3
"""Targeted recovery, not a repeat crawl of the accepted party catalog."""
import concurrent.futures,copy,datetime as dt,html,json,pathlib,re,threading,time,urllib.parse
from bs4 import BeautifulSoup
import collect_party as core,refresh,discover_storefronts as net
from party_additional_research import search_video
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
def load(n,d):
 p=R/'data'/n;return json.loads(p.read_text()) if p.exists() else d
def save(n,d):(R/'data'/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
IDENTITIES={'N++':(230270,['N++ (NPLUSPLUS)']),'Haven':(983970,[]),'Trash Sailors':(1132030,['Trash Sailors: Co-Op Trash Raft Simulator']),'Laser League: World Arena':(570460,[]),'Horizon Chase Turbo':(389140,[]),'LEGO 2K Drive':(1451810,[]),'Hot Wheels Unleashed 2 - Turbocharged':(2051120,[]),'Rubber Royale':(2257640,[]),'JYDGE':(654050,[]),'Scott Pilgrim vs. The World: The Game - Complete Edition':(2215260,[]),'Divinity: Original Sin 2 - Definitive Edition':(435150,['Divinity: Original Sin 2']),'Spelunky':(239350,[]),'Spelunky 2':(418530,[]),'Risk of Rain Returns':(1337520,[]),'TMNT: Wrath of the Mutants':(2463300,['Teenage Mutant Ninja Turtles Arcade: Wrath of the Mutants'])}
PAGES={'thunder':'https://www.typicalentertainment.com/','spider':'https://store.epicgames.com/en-US/p/spiderheck-0fb81d','samurai':'https://samuraigunn2.com/','bopl':'https://www.zapraygames.com/','bopl-native-mod-boundary':'https://thunderstore.io/c/bopl-battle/p/geddesworks/FixedMoreBopl/','rocket-league':'https://store.epicgames.com/en-US/p/rocket-league','sunderfolk':'https://www.dreamhaven.com/games/sunderfolk','gore-cannoli2':'https://www.gunsgoreandcannoli.com/','baldur':'https://baldursgate3.game/','towerfall-dlc':'https://store.steampowered.com/app/337840/','golf-it-hotseat':'https://steamcommunity.com/app/571740/discussions/search/?q=hotseat','steam-armageddon':'https://www.team17.com/games/worms-armageddon/','speedrunners2':'https://www.speedrunners2.com/','sportsfriends':'https://www.sportsfriendsgame.com/'}
LOCK=threading.Lock();NEXT=0

def paced(url):
 global NEXT
 if urllib.parse.urlsplit(url).hostname=='store.steampowered.com':
  with LOCK:delay=max(0,NEXT-time.monotonic());NEXT=max(NEXT,time.monotonic())+1.5
  if delay:time.sleep(delay)
 return core.ORIGINAL_GET(url)
refresh.get=paced
original_load=core.load
core.load=lambda n,d:({'identities':{k:{'appid':v[0],'aliases':v[1]} for k,v in IDENTITIES.items()}} if n=='party-corrections.json' else original_load(n,d))

def inspect(pair):
 key,url=pair
 try:
  raw,final,_=net.read(url);s=BeautifulSoup(raw,'html.parser')
  for n in list(s.select('footer,nav,#comments,.comments')):n.decompose()
  return key,{'sourceUrl':final,'title':s.title.get_text(' ',strip=True) if s.title else '', 'text':s.get_text(' ',strip=True),'youtube':list(dict.fromkeys(re.findall(r'(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})',html.unescape(raw.replace('\\/','/'))))),'checkedAt':NOW}
 except Exception as e:return key,{'sourceUrl':url,'state':'unresolved-active','error':str(e)}

def main():
 primary=load('party-steam.json',{});extra=load('party-extra.json',{});old=load('party-recovered.json',{}).get('items',[]);existing=load('catalog.json',{}).get('items',[]);candidates=[];rows=[];pending=[]
 for d in primary.get('dispositions',[])+extra.get('dispositions',[]):
  if d['state'] not in ['unresolved-active','local-unresolved'] or not d.get('seed'):continue
  if d['candidate'] in ['Nidhogg 3','Lance A Lot','TowerFall Dark World Expansion']:continue
  seed=copy.deepcopy(d['seed']);exact=next((m for m in d.get('matches',[]) if core.norm(m['name'])==core.norm(seed['name'])),None)
  if d.get('appid'):seed['appid']=str(d['appid'])
  elif exact:seed['appid']=str(exact['appid'])
  candidates.append(seed)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for g in pool.map(lambda s:core.collect(s,old,existing,False),candidates):
   if g.get('id'):rows.append(g)
   else:pending.append(g)
   print('RECOVERY',g.get('name',g.get('candidate')),g.get('state'),flush=True)
 # Local-support claims for special cases remain unresolved, while exact identity/media are retained for review.
 special={1086940:'Baldur\'s Gate 3',1094870:'Acron: Attack of the Squirrels!',238530:'Super Puzzle Platformer Deluxe',525510:'Guns, Gore and Cannoli 2'}
 for aid,name in special.items():
  d=next((p for p in pending if p.get('appid')==aid),None)
  if not d:continue
  detail=refresh.details(aid)
  if not detail or core.norm(detail['name'])!=core.norm(name):continue
  seed=d['seed'];g=refresh.resolve({'appid':aid,'name':detail['name'],'fit':seed['fit'],'collection':seed['collection']},{},True)
  if g.get('verification')!='verified':continue
  u=g['steamUrl'];g.update(hubs=[core.HUB],primaryUrl=u,provider='Steam',partyFit=int(seed['fit']),partyCollection=seed['collection'],collections=[seed['collection']],partyEvidence={'sourceUrl':u,'about':refresh.text(detail.get('about_the_game','')),'description':refresh.text(detail.get('short_description','')),'features':g['features']},partyInfo={'countHint':int(seed['countHint']),'modeHint':seed['modeHint'],'countVerified':False,'playerCounts':[],'modes':[],'participation':seed['participation'],'platform':'PC edition','sourceUrl':u,'inputs':'Requires mode review','notes':seed['note'],'requiresInternet':'See exact mode requirements.'},storefronts=[{'url':u,'provider':'Steam','kind':'store','verified':True,'lastChecked':NOW}]);rows.append(g)
 save('party-recovered.json',{'schemaVersion':1,'generatedAt':NOW,'items':rows,'dispositions':pending})
 combined=primary['items']+extra['items']+rows
 # Read only the developer websites of records whose current store text lacks an explicit count phrase.
 for g in combined:
  text=core.normalized_text(g.get('partyEvidence',{}).get('about','')+' '+g.get('summary',''));website=g.get('website')
  if website and not re.search(r'\b[2-9]\b.{0,18}(?:player|local|co.op)|(?:local|co.op).{0,18}\b[2-9]\b|\b1v1\b',text,re.I):
   website=website.replace('http://','https://',1)
   if net.safe(website) and not any(k in website for k in ['twitter.com','x.com','facebook.com','discord.gg','youtube.com']):PAGES[g['id']]=website
 sources={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for k,v in pool.map(inspect,PAGES.items()):sources[k]=v
 save('party-supplemental-evidence.json',{'generatedAt':NOW,'records':sources})
 queries={'steam:238370':'Magicka 2 official launch trailer Paradox','steam:217200':'Worms Armageddon official Team17 trailer','steam:2179180':'Hex Party official game trailer','external:mario-kart-8-deluxe':'Mario Kart 8 Deluxe overview trailer Nintendo of America','external:smash-ultimate':'Super Smash Bros Ultimate overview trailer Nintendo of America'};video={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  def one(x):
   try:return x[0],search_video(x[1])
   except Exception as e:return x[0],{'error':str(e)}
  for k,v in pool.map(one,queries.items()):video[k]=v
 save('party-missing-video-candidates.json',{'generatedAt':NOW,'records':video})
 stores=load('party-recovered-stores.json',{'overrides':{}})
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for ident,v in pool.map(lambda g:core.alternatives(g,stores['overrides'].get(g['id']),True),rows):stores['overrides'][ident]=v
 save('party-recovered-stores.json',stores)
 print(json.dumps({'recovered':len(rows),'remainingCandidates':[(p.get('candidate'),p.get('reason')) for p in pending],'sourcePages':len(sources)},indent=2))
if __name__=='__main__':main()
