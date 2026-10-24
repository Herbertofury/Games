"""Two native wiki homes built from the same canonical survival records."""
import copy,collections,json
from catalog_model import game_key,score
HUBS={'Survival':('Survival','Survival-Media','Make a place in a wild world.'),'Minecraft-like worlds':('Minecraft-Like-Worlds','Minecraft-Like-Media','A world worth making your own.')}
def build(root,catalog):
 from wiki_builder import table,media_atlas,link,rank,m
 out=root/'wiki';allrows=[]
 for hub,(slug,atlas,title) in HUBS.items():
  rows=[]
  for g in catalog['items']:
   if hub not in g.get('hubs',[]):continue
   x=copy.deepcopy(g);x['collection']=g.get('survivalCollection',g['collection']);x['fit']=g.get('survivalFit',g.get('fit'));rows.append(x)
  if not rows:continue
  allrows+=rows;counts=collections.Counter(g['status'] for g in rows);links=sum(len(g.get('storefronts',[])) for g in rows)
  intro=f'# {hub}: {title}\n\n**[Interactive library]({link({"hub":hub})})** | [Complete image and video atlas]({atlas}) | [Portable HTML](https://github.com/Herbertofury/Games/releases/latest) | [Survival field guide](Survival-Field-Guide)\n\n'
  intro+=f'**{len(rows)} unique games and projects, {len({g["collection"] for g in rows})} collections, {links} confirmed distribution references.** '+', '.join(f'{n} {s.lower()}' for s,n in sorted(counts.items()))+'. Overlapping genre memberships are one shared game identity, not duplicate recommendations.\n\n'
  intro+=('Conan, ARK and Windrose are the starting point: gather resources, build a home, explore, fight, and make a world with friends. Tactical, colony and automation neighbors remain explicitly labelled.\n\n' if hub=='Survival' else 'Minecraft, Terraria, Hytale and Vintage Story define this separate category: editable worlds, mining, construction, crafting and long-term discovery. Voxel RPGs and factory sandboxes are labelled neighbors, not falsely described as the same survival loop.\n\n')
  picks=sorted([g for g in rows if not g.get('comingSoon') and (score(g) or 0)>=8 and g['status'] not in ['Prototype','Demo']],key=rank)
  intro+='## Where to start\n\n'+media_atlas(picks[:12],hub)
  routes=[('Playable now',{'playable':'true'},'Released and accessible development builds, with their exact statuses visible.'),('Strongest fit',{'fit':'8','playable':'true'},'Editorial fit is checked against review reception and sample size.'),('Newest discoveries',{'tag':'Recent survival release','playable':'true','sort':'newest'},'2025-2026 store releases with confirmed earlier access excluded. Original non-Steam dates may be earlier; inspect the title chronology.'),('Co-op',{'coop':'true','playable':'true'},'Co-op explicitly listed in the source. Cross-play and server rules are separate.'),('Single-player listed',{'tag':'Single-player listed','playable':'true'},'A single-player listing is not a guarantee of fully offline access.'),('Outside Steam',{'offSteam':'true'},'Confirmed alternate stores and creator projects.'),('Demos',{'demo':'true'},'Actual demo destinations attached to their game, not duplicate games.'),('Watchlist',{'status':'Upcoming'},'Unreleased full games, clearly separated.')]
  intro+='## Choose the kind of world\n\n| Route | What it means |\n|:--|:--|\n'
  for name,params,note in routes:intro+=f'| [{name}]({link(dict(hub=hub,**params))}) | {note} |\n'
  intro+='\n## The full collection\n\n'
  for col in sorted({g['collection'] for g in rows}):intro+='### '+col+'\n\n'+table(sorted([g for g in rows if g['collection']==col],key=rank))
  intro+='\n## Future worlds, not finished releases\n\n'+table(sorted([g for g in rows if g.get('comingSoon')],key=rank))
  intro+='\n## Evidence boundaries\n\nEvery published entry has artwork, an exact video source and a confirmed distribution destination. Store coverage is the confirmed set, not every worldwide reseller. Scores retain their provider and review count. Creator support is not a game license; an engine is not a standalone survival game. [Scoring details](Ratings-and-Sources).\n'
  (out/(slug+'.md')).write_text(intro)
  (out/(atlas+'.md')).write_text(f'# {hub}: the complete visual atlas\n\n**{len(rows)} entries.** Every game below links its exact imagery, video source, and confirmed distribution pages. The wiki displays artwork and video links; the interactive app supplies in-page players.\n\n[Recommendations]({slug}) | [Interactive players]({link({"hub":hub})}) | [Portable HTML](https://github.com/Herbertofury/Games/releases/latest)\n\n'+media_atlas(sorted(rows,key=rank),hub))
  for g in rows:
   p=out/(game_key(g)+'.md');text=p.read_text();info=g.get('survivalInfo',{})
   text+=f'\n## Survival field notes\n\n[Back to {hub}]({slug})\n\n'
   for k,label in [('world','World and systems'),('solo','Solo'),('coop','Co-op'),('hosting','Hosting'),('modding','Modding'),('terrain','Terrain and building')]:text+='**'+label+':** '+m(info.get(k))+'\n\n'
   text+=m(info.get('basis'))+'\n\n'
   if g.get('earlyAccessReleaseDate'):text+='**Steam Early Access:** '+m(g['earlyAccessReleaseDate'])+'; **store/full-release milestone:** '+m(g.get('releaseDate') or g.get('releaseLabel'))+'. These are separate dates, not separate games.\n\n'
   if g.get('survivalWhy'):text+='**Why it is here:** '+m(g['survivalWhy'])+'\n'
   p.write_text(text)
 if not allrows:return
 providers=collections.Counter(x['provider'] for g in {g['id']:g for g in allrows}.values() for x in g.get('storefronts',[]))
 (out/'Survival-Field-Guide.md').write_text('''# Survival field guide

[Survival](Survival) | [Minecraft-like worlds](Minecraft-Like-Worlds)

## Find the right kind of long-term world

**Conan / ARK / Windrose:** character-led survival crafting, expeditions, bases and combat. PvE co-op and PvP servers can be dramatically different experiences; read the exact server rules before joining.

**Minecraft / Terraria / Hytale / Vintage Story:** terrain, mining, crafting and construction are the central attraction. Terraria-like 2D games have their own collection. Voxel art alone does not make a game a survival builder.

**Adjacent, not interchangeable:** automation games, colony management, survival driving and creature-survival MMOs have dedicated shelves. Their inclusion is a labelled detour, not a claim that every game plays like Minecraft or Conan.

## Before buying or starting a server

A Steam single-player label is not proof of offline play. Co-op does not imply cross-play, split-screen, private dedicated servers, a particular player limit, or save compatibility. Dedicated-server and modding flags record explicit source mentions only. Check the official instructions for the exact edition and build.

Released, Early Access, prototypes, demos and upcoming games remain distinct. Old originals and new editions are dated separately where verified. Steam's separately labelled Early Access launch is shown alongside a later 1.0/store milestone. Confirmed pre-2025 access is excluded from the recent-discoveries shortcut; a missing history label is not proof of no earlier non-Steam release. Prices are dated US store snapshots, not live offers.

## Creator-hosted games

Minecraft Java and Bedrock are separate editions. Hytale and Vintage Story use their own official distribution. Luanti is the free engine used by VoxeLibre and Mineclonia, not another survival game to inflate the list. Support memberships and archived storefront pages are clearly marked. Prefer active official purchase/download routes.

## Research and updates

The source repository retains candidate dispositions, unresolved names, store-check dates, exact media provenance and prior IDs. No-result does not mean a game or store does not exist. Only confirmed recommendations enter the published hubs. No scheduled crawler is enabled.

### Confirmed per-game source references

'''+''.join(f'- {p}: {n}\n' for p,n in sorted(providers.items())))
 home=out/'Home.md';text=home.read_text();text=text.replace('# A home for every great discovery','# A home for every great discovery\n\n**NEW: [Survival](Survival) | [Minecraft-like worlds](Minecraft-Like-Worlds) | [Survival media](Survival-Media) | [Minecraft-like media](Minecraft-Like-Media)**',1);home.write_text(text)
 p=out/'_Sidebar.md';p.write_text(p.read_text().replace('- [Home](Home)','- [Home](Home)\n- [Survival](Survival)\n- [Minecraft-like worlds](Minecraft-Like-Worlds)\n- [Survival: complete media atlas](Survival-Media)\n- [Minecraft-like: complete media atlas](Minecraft-Like-Media)\n- [Survival field guide](Survival-Field-Guide)',1))
