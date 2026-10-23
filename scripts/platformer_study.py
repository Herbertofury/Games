"""Generate every platformer view from the same assembled canonical snapshot."""
from __future__ import annotations
import collections,csv,hashlib,html,json,pathlib,re,urllib.parse
from catalog_model import game_key,primary,score
from wiki_builder import m,link,rating,rank,table,video_url
HUB='Platformers'
REPO='https://github.com/Herbertofury/Games'
NAV='[Platformer hub](Platformers) | [Comparative study](Platformers-Study) | [Gem shortlist](Platformers-Gems) | [New and upcoming](Platformers-New-and-Upcoming) | [Media atlas](Platformers-Media) | [Source and coverage audit](Platformers-Sources)\n\n'
LENSES={
 'Precision & mastery':('Make each attempt teach you something.','Compare momentum, checkpoint frequency, movement constraints and the cost of a mistake. Difficulty alone is not a genre or a recommendation.'),
 'Speed & expressive movement':('Find a line worth repeating.','Momentum, grappling, aerial control and route optimization. First-person, shooter and vehicle hybrids are explicitly labelled in their dossiers.'),
 '3D worlds & collectathons':('Learn a place by moving through it.','Authored courses, compact retro worlds and open movement playgrounds. Check camera feel, optional completion demands and the exact edition.'),
 'Puzzles & cinematic journeys':('Understand the space before crossing it.','Logical systems, physics puzzles and deliberately paced cinematic adventures. Atmosphere and narrative are not evidence of precision-platforming depth.'),
 'Exploration & Metroidvanias':('Return with a different understanding.','Ability-led routes, secrets and connected maps. Combat-heavy, top-down and survival-adjacent inclusions retain their scope labels.'),
 'Action & retro adventures':('Movement and encounters, authored together.','Modern-retro campaigns, ninja action, character abilities and clearly marked run-and-gun neighbors. Classic collections are exact store products, counted once.'),
 'Roguelite platformers':('Make the next run more deliberate.','Procedural uncertainty, execution and progression. These records also appear in Roguelites without duplicating their stable identity.'),
 'Co-op & playful chaos':('Movement becomes a conversation.','Authored collaboration, demanding coordination and competitive stage-building. Local, online, player-count and pass requirements are edition-specific.'),
 'Colorful & approachable':('Curiosity first; challenge by choice.','Characterful adventures and approachable starting routes. Cute presentation is neither an age rating nor an accessibility guarantee.'),
 'Free creator releases':('Small experiments, real discoveries.','Official creator releases and open-source projects. Hardware-included software and free PC/browser downloads are not conflated.'),
}

def slug(value):return re.sub('[^A-Za-z0-9]+','-',value).strip('-')
def has_video(g):return any(any(t.get(k) for k in ('mp4','webm','hls','youtube')) for t in g.get('trailers',[]))
def dossier(g):return '['+m(g['name'])+']('+game_key(g)+')'
def section_table(rows):return table(sorted(rows,key=rank)) if rows else '_No accepted entries in this snapshot._\n'
def write(out,name,text):(out/(name+'.md')).write_text(text,encoding='utf-8')

def build_platformer_wiki(root,catalog):
 root=pathlib.Path(root);out=root/'wiki';rows=[g for g in catalog['items'] if HUB in g.get('hubs',[])];assert rows
 out.mkdir(exist_ok=True);assets=root/'dist/assets';assets.mkdir(parents=True,exist_ok=True)
 groups=collections.defaultdict(list)
 for g in rows:groups[g['platformerCollection']].append(g)
 checked=max(str(g.get('researchCheckedAt') or g.get('verifiedAt') or '') for g in rows)
 unresolved=json.loads((root/'data/platformers-steam.json').read_text()).get('unresolved',[])
 review_gaps=[g for g in rows if g.get('steamUrl') and g.get('reviewError')]
 media_gaps=[{'id':g['id'],'name':g['name'],'artworkMissing':not bool(g.get('image')),'videoMissing':not has_video(g),'source':primary(g)} for g in rows if not g.get('image') or not has_video(g)]
 gems=[g for g in rows if g.get('hiddenGem') and 'Platformer gem shortlist' in g.get('tags',[])]
 upcoming=[g for g in rows if g.get('comingSoon') or g.get('status')=='Upcoming']
 early=[g for g in rows if g.get('status')=='Early Access' and not g.get('comingSoon')]
 recent=[g for g in rows if g.get('status')=='Released' and (g.get('releaseDate') or '')>='2025-01-01']
 report={'schemaVersion':1,'studyDate':'2026-10-23','checkedThrough':checked,'records':len(rows),'steam':sum(bool(g.get('steamUrl')) for g in rows),'external':sum(not g.get('steamUrl') for g in rows),'released':sum(g.get('status')=='Released' for g in rows),'earlyAccess':len(early),'upcoming':len(upcoming),'recentReleasedEditionsSince2025':len(recent),'collections':{k:len(v) for k,v in sorted(groups.items())},'gemShortlist':len(gems),'individualEditorialNotes':sum(g.get('platformerInfo',{}).get('editorialDepth')=='Individual editorial note' for g in rows),'withArtwork':sum(bool(g.get('image')) for g in rows),'withPlayableVideoMetadata':sum(has_video(g) for g in rows),'screenshots':sum(len(g.get('screenshots',[])) for g in rows),'crossGenreIds':[g['id'] for g in rows if any(h not in ['Platformers','Roguelites'] for h in g.get('hubs',[]))],'unresolved':unresolved,'reviewRefreshGaps':[g['id'] for g in review_gaps],'mediaGaps':media_gaps,'recordIds':[g['id'] for g in rows],'datasetHash':catalog['build']['datasetHash'],'claimLimits':['Not an exhaustive inventory of all platformers.','Not a hands-on playtest or completion claim.','Steam platforms are PC operating systems, not a complete console-port inventory.','Playable video metadata is distinct from a successful playback test.','Recent dates can refer to newer store editions of older games.']}
 (root/'data/platformers-study-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="470" viewBox="0 0 1600 470"><defs><linearGradient id="bg"><stop stop-color="#10292f"/><stop offset="1" stop-color="#10171e"/></linearGradient></defs><rect width="1600" height="470" fill="url(#bg)"/><g fill="none" stroke="#76b6b4" stroke-opacity=".35"><path d="M930 370H1070V300H1210V220H1350V130H1510" stroke-width="4"/><path d="M960 360Q1090 120 1225 205T1490 110" stroke-width="3" stroke-dasharray="7 12"/></g><circle cx="1225" cy="205" r="18" fill="#a0e8dc"/><text x="92" y="93" fill="#9ce6e2" font-family="Arial,sans-serif" font-size="18" letter-spacing="5">GAMES / THE FOURTH COLLECTION</text><text x="85" y="231" fill="#f5f8f5" font-family="Arial,sans-serif" font-size="100" font-weight="700" letter-spacing="-5">Make the leap.</text><text x="92" y="301" fill="#b3c8c8" font-family="Arial,sans-serif" font-size="26">Precision. Playful worlds. Impossible routes.</text><text x="92" y="385" fill="#76a29f" font-family="Arial,sans-serif" font-size="19">SOURCE-GROUNDED DISCOVERY / CLASSICS TO CURRENT RELEASES</text></svg>'''
 (assets/'platformers-banner.svg').write_text(svg)
 banner='![Platformers: make the leap]('+REPO+'/raw/main/dist/assets/platformers-banner.svg)\n\n'
 overview=f"**{len(rows)} accepted records across {len(groups)} routes:** {report['steam']} Steam identities and {report['external']} console/creator releases. {report['released']} released, {len(early)} Early Access and {len(upcoming)} upcoming. Cross-genre games retain one stable ID.\n\n"
 body=banner+'# Platformers\n\n'+NAV+overview+'**[Open the interactive platformer collection]('+link({'hub':HUB})+')**\n\n'
 body+='This is a curated discovery study, not an exhaustive inventory or a claim of hands-on playtesting. Recommendations, community reception and your personal rating remain separate.\n\n## Choose your route\n\n| Route | Accepted records | Study lens |\n|:--|--:|:--|\n'
 for name,items in groups.items():body+='| ['+m(name)+'](Platformers-'+slug(name)+') | '+str(len(items))+' | '+m(LENSES[name][0])+' |\n'
 body+='\n## A few useful starting points\n\n'
 featured=['steam:504230','steam:1599020','steam:1533420','steam:2365810','steam:813230','steam:1221480','steam:1672810','external:astro-bot']
 by={g['id']:g for g in rows}
 for ident in featured:
  if ident not in by:continue
  g=by[ident];body+='### '+dossier(g)+'\n\n'+m(g.get('platformerWhy') or g['summary'])+'\n\n**Before choosing:** '+m(g.get('platformerCaution'))+'\n\n'
 body+='## Complete platformer index\n\n'+section_table(rows)
 body+='\n## Evidence and coverage\n\n'+f"Artwork metadata is available for {report['withArtwork']} records; playable-video metadata for {report['withPlayableVideoMetadata']}. The atlas and source audit disclose every gap. Individual editorial notes cover {report['individualEditorialNotes']} records; other entries use a labelled subgenre study lens alongside verified official facts.\n\nRead [the complete study](Platformers-Study), [source limitations](Platformers-Sources), and [new releases separately from the watchlist](Platformers-New-and-Upcoming).\n"
 write(out,'Platformers',body)
 study=(root/'docs/PLATFORMERS-STUDY.md').read_text();write(out,'Platformers-Study',NAV+study+'\n\n---\n\n'+overview)
 for name,items in groups.items():
  title,description=LENSES[name]
  text=NAV+'# '+m(name)+'\n\n## '+title+'\n\n'+description+'\n\n'+section_table(items)
  text+='\n## Field notes\n\n'
  for g in sorted(items,key=rank):text+='### '+dossier(g)+'\n\n'+m(g.get('platformerWhy'))+'\n\n**Caution:** '+m(g.get('platformerCaution'))+'\n\n**Scope:** '+m(g['platformerInfo'].get('focus'))+' · **Editorial depth:** '+m(g['platformerInfo']['editorialDepth'])+'\n\n[Exact official source]('+primary(g)+') · [Media and details]('+link({'game':g['id']})+')\n\n'
  write(out,'Platformers-'+slug(name),text)
 gemtext=NAV+'# Platformer gem shortlist\n\nThese are editorial discovery leads, not an objective definition of obscurity. The shortlist requires a reviewed candidate, editorial fit at least 8, at least 80% positive in the checked Steam review snapshot, 30–5,000 reviews, no review-refresh error and a non-upcoming state. The broader study includes worthwhile discoveries outside that window.\n\n'+section_table(gems)
 write(out,'Platformers-Gems',gemtext)
 text=NAV+'# New releases, Early Access and the watchlist\n\nA recent store date can be a remaster, port or collection of older games. It does not automatically describe a new original. Dates and purchase availability are snapshots, not guarantees.\n\n## Released store editions from 2025 onward\n\n'
 text+=table(sorted(recent,key=lambda g:g.get('releaseDate',''),reverse=True))+'\n## Early Access — playable, unfinished\n\n'+section_table(early)+'\n## Upcoming — no current purchase recommendation\n\n'+section_table(upcoming)
 write(out,'Platformers-New-and-Upcoming',text)
 atlas=NAV+'# Every platformer: illustrated media atlas\n\nOne entry per stable identity. Artwork and videos retain their exact official source. A source link without a stream is an honest gap, not an invented playable video. GitHub Markdown links video; the interactive library supplies players where supported.\n\n'
 for name,items in groups.items():
  atlas+='## '+m(name)+'\n\n'
  for g in sorted(items,key=lambda g:g['name'].casefold()):
   atlas+='### '+dossier(g)+'\n\n'
   if g.get('image'):atlas+='[!['+m(g['name'])+']('+g['image']+')]('+primary(g)+')\n\n'
   else:atlas+='_Exact artwork is not available in this snapshot; no substitute image is used._\n\n'
   atlas+=m(g.get('platformerWhy'))+'\n\n**'+m(g['status'])+'** · '+m(g.get('releaseLabel'))+' · '+m(rating(g))+'\n\n'
   vids=[t for t in g.get('trailers',[]) if any(t.get(k) for k in ('mp4','webm','hls','youtube'))]
   if vids:atlas+=' | '.join('['+m(t.get('name') or 'Source video')+']('+video_url(t,g)+')' for t in vids)+'\n\n'
   else:atlas+='_No independently collected playable stream. [Check the exact official page]('+primary(g)+') for current videos._\n\n'
   atlas+='[Open interactive gallery]('+link({'game':g['id']})+') · [Full dossier]('+game_key(g)+') · [Official source]('+primary(g)+')\n\n'
 write(out,'Platformers-Media',atlas)
 audit=NAV+'# Platformer source and coverage audit\n\n```json\n'+json.dumps({k:v for k,v in report.items() if k not in ['recordIds','mediaGaps','unresolved']},ensure_ascii=False,indent=2)+'\n```\n\n## Missing media is explicit\n\n| Game | Artwork | Playable-video metadata | Exact source |\n|:--|:--|:--|:--|\n'
 for gap in media_gaps:audit+='| '+dossier(by[gap['id']])+' | '+('Missing' if gap['artworkMissing'] else 'Present')+' | '+('Missing' if gap['videoMissing'] else 'Present')+' | [Official page]('+gap['source']+') |\n'
 audit+='\n## Discovery reconciliation\n\n'
 audit+=json.dumps(unresolved,ensure_ascii=False,indent=2) if unresolved else 'All candidates in the current bounded discovery ledger resolved to an accepted exact identity. This is not a claim that the genre itself is exhaustively covered.'
 audit+='\n\n## Repeatable sources\n\nThe discovery ledger, current-title aliases, official provider snapshots and individual editorial notes are separate source files. See [the updating guide](Updating-the-Library). A page-verification timestamp, a downloaded image and an actually played video are different kinds of evidence; browser QA records the last two separately.\n'
 write(out,'Platformers-Sources',audit)
 # Existing builder creates all dossiers; add scope/hardware evidence without
 # replacing the old source panels, galleries or cross-genre material.
 for g in rows:
  p=out/(game_key(g)+'.md');s=p.read_text();mark='\n## Platformer field notes\n'
  if mark in s:s=s.split(mark)[0]
  info=g['platformerInfo'];s+=mark+'\n**Movement focus:** '+m(info['focus'])+'\n\n**Scope:** '+m(info['scope'])+'\n\n**Verified hardware / builds:** '+m(', '.join(g.get('platforms',[])) or 'See the exact official page')+'\n\n'+m(g.get('platformerWhy'))+'\n\n**Before choosing:** '+m(g.get('platformerCaution'))+'\n\n**Evidence depth:** '+m(info['editorialDepth'])+'. '+m(info['selectionBasis'])+' '+m(info.get('platformScope'))+'\n\n'+NAV
  p.write_text(s)
 p=out/'Home.md';s=p.read_text();s=s.replace('**[Open your interactive library]', '[Platformers](Platformers) · [Platformer study](Platformers-Study) · [Platformer media atlas](Platformers-Media)\n\n**[Open your interactive library]',1);s=s.replace('Cross-genre games appear',str(len(rows))+' in Platformers. Cross-genre games appear',1);p.write_text(s)
 p=out/'_Sidebar.md';s=p.read_text();s=s.replace('- [Home](Home)','- [Home](Home)\n- [Platformers](Platformers)\n- [Platformer study](Platformers-Study)\n- [Platformer gems](Platformers-Gems)\n- [Platformer new / upcoming](Platformers-New-and-Upcoming)\n- [Every platformer: media atlas](Platformers-Media)',1);p.write_text(s)
 with (root/'data/platformers-index.csv').open('w',encoding='utf-8-sig',newline='') as f:
  fields=['id','name','route','scope','status','storeEditionRelease','editorialRecommendation','communityReception','hardwareOrBuilds','officialSource','why','caution','editorialDepth'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
  for g in rows:writer.writerow({'id':g['id'],'name':g['name'],'route':g['platformerCollection'],'scope':g['platformerInfo']['focus'],'status':g['status'],'storeEditionRelease':g.get('releaseDate') or g.get('releaseLabel'),'editorialRecommendation':score(g),'communityReception':rating(g),'hardwareOrBuilds':'; '.join(g.get('platforms',[])),'officialSource':primary(g),'why':g.get('platformerWhy'),'caution':g.get('platformerCaution'),'editorialDepth':g['platformerInfo']['editorialDepth']})
 print('Platformer study generated:',json.dumps({k:report[k] for k in ['records','released','earlyAccess','upcoming','individualEditorialNotes','withArtwork','withPlayableVideoMetadata']}))
