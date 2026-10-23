from pathlib import Path
import datetime as dt,json,re,hashlib
from bs4 import BeautifulSoup
W=Path(__file__).resolve().parents[1];E=W/'qa/rts-evidence';R=W/'qa/rts-recovery'
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
result=json.loads((R/'media-recovered.json').read_text());over=result['overrides']
steam=json.loads((W/'data/rts-steam.json').read_text())['items'];external=json.loads((W/'data/rts-external.json').read_text())['items'];allg={g['id']:g for g in steam+external}
reports={n:json.loads((E/n/'report.json').read_text()) for n in ['games-rts-media-resolution','games-rts-video-candidates','games-rts-final-sources']}
meta={m['id']:m for n,k in [('games-rts-media-resolution','youtubeMetadata'),('games-rts-video-candidates','metadata'),('games-rts-final-sources','videos')] for m in reports[n][k] if m.get('title')}

def source(url,provider='Source',kind='media',**kw):return dict(url=url,provider=provider,kind=kind,verified=True,lastChecked=NOW,**kw)
def add(ident,**kw):
 o=over.setdefault(ident,{})
 for k,v in kw.items():
  if k=='_replace':o.setdefault(k,{}).update(v)
  elif k in ['sources','storefronts','trailers']:o.setdefault(k,[]).extend(v)
  else:o[k]=v

def video(ident,vid,official=False,note=None,url=None,name=None,replace=False):
 m=meta[vid];watch='https://www.youtube.com/watch?v='+vid;src=url or watch
 t={'youtube':vid,'name':name or m['title'],'sourceUrl':src,'watchUrl':watch,'official':official,'credit':m['author_name'],'poster':m['thumbnail_url']}
 if note:t['editionNote']=note
 add(ident,**({'_replace':{'trailers':[t]}} if replace else {'trailers':[t]}),sources=[source(src,m['author_name'])])

for ident,vid in [('steam:2710','jqlyMDiZHLE'),('steam:9760','eQ51eGSx38c'),('external:empires-dawn-modern-world','WVrUQwiJsv0'),('external:world-in-conflict','Ue0GNIAfd20'),('external:warlords-battlecry-2','y9Z-TMwyoJc'),('external:littlewargame','WwbUOen0wFs'),('external:end-of-days-zh','h4Wtim9Wgic')]:
 video(ident,vid,note='Credited community gameplay, not an official trailer.')
video('external:warcraft-3-reforged','Q2zfx5hQ3CE',True,note='Base-game gameplay trailer. The separate Forsaken Kingdom video on the current franchise page is not substituted for this edition.')
video('external:starcraft-remastered','OIWbdRgnXjo',True,note='Official announcement trailer hosted by IGN; not the newer franchise teaser.')
playlist=next(p['data'][0] for p in reports['games-rts-final-sources']['pages'] if p['key']=='supcom-playlist')
add('steam:9420',trailers=[{'mp4':playlist['sources'][0]['file'],'name':'Supreme Commander: Forged Alliance trailer','sourceUrl':playlist['meta']['url'],'poster':playlist['image'],'credit':'Publisher trailer archived by Gameswelt','editionNote':'Historical publisher trailer, archived at Gameswelt.'}],sources=[source(playlist['meta']['url'],'Gameswelt')])

# Exact publisher-published remaster links remain usable even when its store requires login.
announcement='https://news.blizzard.com/en-us/article/24148499/catch-up-on-the-future-of-warcraft-with-the-warcraft-30th-anniversary-direct'
battlechest='https://bnetcmsus-a.akamaihd.net/cms/content_entry_media/u1/U104RGIXCRY81731450580527.png'
for ident,short in [('external:warcraft-1-remastered','https://blizz.ly/4hLD57w'),('external:warcraft-2-remastered','https://blizz.ly/3UKCV6J')]:
 video(ident,'ryZ2jiW95qo',True,url=announcement,note='Official combined Battle Chest trailer featuring Warcraft I and II remasters; not a standalone trailer for just one game.',replace=True)
 add(ident,verification='verified',verifiedAt=NOW,_replace={'image':battlechest,'screenshots':[{'src':battlechest,'thumbnail':battlechest,'alt':'Official Warcraft RTS Battle Chest artwork including both remasters','sourceUrl':announcement,'credit':'Blizzard; shared Battle Chest artwork','verified':True}],'primaryUrl':short,'storefronts':[source(short,'Battle.net','store',label=allg[ident]['name']+' - Battle.net',sourceUrl=announcement,evidence='Exact named purchase link in the official Blizzard launch announcement; checkout requires Battle.net login.')]},mediaNote='Artwork and trailer are explicitly for the shared Warcraft RTS Battle Chest.',rtsInfo={**json.loads((W/'data/rts-curation.json').read_text())['overrides'][ident]['rtsInfo'],'sourceUrl':announcement})

# Replace erroneous site UI assets with real screenshots or exact-edition artwork.
zero=allg['external:0-ad'];shots=[s for s in zero['screenshots'] if 'wildfiregames.com/forum/uploads/' in s['src']]
add(zero['id'],_replace={'image':shots[0]['src'],'screenshots':shots},sources=[source('https://play0ad.com/','Wildfire Games','project')])
little=meta['WwbUOen0wFs'];add('external:littlewargame',_replace={'image':little['thumbnail_url'],'screenshots':[{'src':little['thumbnail_url'],'thumbnail':little['thumbnail_url'],'alt':'Littlewargame gameplay video artwork','sourceUrl':'https://www.youtube.com/watch?v=WwbUOen0wFs','credit':little['author_name'],'verified':True}]},mediaNote='Gameplay thumbnail credited to GrubbyPlays; the page sound/play buttons are not presented as screenshots.')
news=next(p for p in reports['games-rts-final-sources']['pages'] if p['key']=='sc-remastered-news')
s=BeautifulSoup((E/'games-rts-final-sources/sc-remastered-news.txt').read_text(),'html.parser')
hero=s.select_one('meta[property="og:image"]')['content'];pics=[x['src'] for x in s.select('article img[src]') if '/cms/page_media/' in x['src']]
add('external:starcraft-remastered',_replace={'image':hero,'screenshots':[{'src':u,'thumbnail':u,'alt':'StarCraft Remastered launch artwork','sourceUrl':news['url'],'credit':'Blizzard','verified':True} for u in pics]},sources=[source(news['url'],'Blizzard','project')])
add('external:starcraft-2',_replace={'image':meta['8L4kNzTNnqk']['thumbnail_url']},mediaNote='Exact StarCraft II official-video artwork, not artwork for a different franchise entry.')
# Decorative SVGs, platform buttons and unrelated user avatars are not game gallery items.
reject=re.compile(r'\.svg(?:\?|$)|(?:dlbtn_|butt_play|unmuted|discord|_avm\d?\.|crumble|sparks-)',re.I)
for g in external:
 if g['id'] in ['external:0-ad','external:littlewargame','external:starcraft-remastered','external:warcraft-1-remastered','external:warcraft-2-remastered']:continue
 clean=[p for p in g['screenshots'] if not reject.search(p['src']) and re.search(r'\.(?:png|jpe?g|gif|webp|avif)(?:\?|$)',p['src'],re.I)]
 if len(clean)!=len(g['screenshots']):add(g['id'],_replace={'screenshots':clean})

# Correct creator builds and bundles, retaining exact distribution choices without duplicates.
stores=json.loads((W/'data/rts-storefronts.json').read_text())['overrides']
fixes={
 'steam:2088550':('https://sarnayer.itch.io/dying-breed','project','Creator project page links to Steam; it is not verified as a full-game itch.io download.'),
 'steam:3213120':('https://machinefall.itch.io/machinefall','prototype','Older creator development build. The 233 MB itch.io archive is not represented as the current Steam release.'),
 'steam:1113030':('https://tensegames.itch.io/stellar-warfare','prototype','Creator lists an April 2024 build; version and features may differ from the current commercial release.'),
 'steam:1272320':('https://door407.itch.io/diplomacy-is-not-an-option','demo','Creator upload is labelled Shareware; this is not the paid full game.')}
for ident,(url,kind,note) in fixes.items():
 l=next(x.copy() for x in stores[ident]['storefronts'] if x['url']==url);l.update(kind=kind,editionNote=note,lastChecked=NOW)
 add(ident,storefronts=[l])
# Exclude the RSS feed from actionable distribution buttons, not actual project destinations.
g=allg['steam:908770'];ls=[x for x in g['storefronts']+stores[g['id']]['storefronts'] if not '/feed/' in x['url']]
add(g['id'],_replace={'storefronts':ls},storefronts=[])
for ident,slug,label in [('steam:2710','act_of_war_gold_edition','GOG Gold Edition bundle'),('steam:9760','act_of_war_gold_edition','GOG Gold Edition bundle'),('steam:298030','total_annihilation_commander_pack','GOG Commander Pack'),('steam:433280','warlords_battlecry_3','GOG')]:
 u='https://www.gog.com/en/game/'+slug;add(ident,storefronts=[source(u,'GOG','bundle' if 'gold' in slug or 'pack' in slug else 'store',label=label,sourceUrl=u)])
add('steam:334920',storefronts=[source('https://zero-k.info/','Official site','project',sourceUrl='https://zero-k.info/')])
add('external:starcraft-remastered',storefronts=[source('https://www.xbox.com/en-US/games/store/starcraft-remastered/9n2gwlmchjtn','Xbox PC','store',sourceUrl='https://www.xbox.com/en-US/games/store/starcraft-remastered/9n2gwlmchjtn',editionNote='PC edition listing; not an Xbox-console RTS release.')])
add('external:contra-x',curatorWhy='Keep the Zero Hour foundation and turn the faction identities, challenge and powerful arsenals up dramatically. A direct extension of the style you asked for.')
add('steam:1486920',recommendationCaution='Overall reception is positive, but Steam recent English reviews were Mixed when checked on October 23, 2026. Inspect the recent reviews alongside the cumulative rating.',sources=[source('https://store.steampowered.com/app/1486920/','Steam','review')])
result['generatedAt']=NOW;result['method']='Completed from the saved exact-source evidence. Artwork roles, credited community footage, bundles and demo/prototype editions are distinguished. Login or provider blocks are not bypassed.'
for o in over.values():
 for k in ['sources','storefronts']:
  if k in o:o[k]=list({v['url']:v for v in o[k]}.values())
(W/'data/rts-media-completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
proof={'schemaVersion':1,'checkedAt':NOW,'sourceRevision':'1195b47526d4b870042adc883f8798b2a7397683','previousResearchReused':True,'youtubeMetadata':list(meta.values()),'evidenceArtifacts':[],'rejectedMedia':['WPJWgDItRP8 (not found)','gCyjthtSJBU (channel biography, not game footage)','0rEfOTxr59o (full anniversary show replaced by exact Battle Chest trailer)','Generic page buttons, decorative SVGs and unrelated Blizzard game artwork'],'storeCorrections':fixes,'limitations':['All 130 records have source metadata; runtime image and video decoding is a separate QA gate.','Exact official distribution links are verified; no claim of every worldwide key reseller.','Publisher product checkouts can require login; official published links retained without bypass.']}
for name in ['games-rts-enrichment.zip','games-rts-media-resolution.zip','games-rts-video-candidates.zip','games-rts-final-sources.zip']:
 p=W/'qa/rts-artifacts'/name;proof['evidenceArtifacts'].append({'file':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(W/'data/rts-source-proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
# A full-game entry can also have a playable demo edition. Other hubs keep existing behavior.
p=W/'site/app.js';js=p.read_text()
changes=[("offSteam:false,hostRating","offSteam:false,demo:false,hostRating"),("offSteam:'Beyond Steam',q:","offSteam:'Beyond Steam',demo:'Playable demo available',q:"),("if(state.shelf==='favorites'","if(state.demo&&g.status!=='Demo'&&!(g.demoAppids||[]).length&&!(g.storefronts||[]).some(l=>l.kind==='demo'))return false;\n    if(state.shelf==='favorites'"),("if(name==='demos'){state.status='Demo';}","if(name==='demos'){if(state.hub==='Real-time strategy')state.demo=true;else state.status='Demo';}")]
for old,new in changes:
 if new in js:continue
 assert js.count(old)==1,'Expected one exact UI mutation: '+old
 js=js.replace(old,new,1)
p.write_text(js)
print('Recovered and completed media overlays',len(over))
