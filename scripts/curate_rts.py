#!/usr/bin/env python3
"""Editorial, evidence-aware RTS curation. Facts remain in provider snapshots."""
import datetime as dt,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
WHY={
1486920:'The first modern purchase I would investigate for the C&C feeling: a proper construction economy, distinctive armies and a campaign-driven presentation. A much closer fit than a tactical game without bases.',
318020:'One of the closest modern-military relatives of Generals, including resource harassment and asymmetrical armies. The Reboot overhaul is for skirmish/multiplayer; launch the original game for its campaign. Reception is mixed, so similarity does not equal a blanket quality endorsement.',
1439750:'A particularly good pick for fast base building, cooperative play and a large toy-box battlefield. The chunky visual style is deliberate; the appeal is commanding a lot of destructive machinery without a cumbersome interface.',
427250:'A compact, immediately approachable C&C-style army builder. Start here for uncomplicated skirmishes rather than cinematic storytelling or realistic military hardware.',
497850:'The fantasy sibling of 8-Bit Armies. Useful when you want the same straightforward base-building rhythm with monsters and magic instead of modern tanks.',
531680:'The sci-fi branch of the 8-Bit series. Worth considering alongside Armies and Hordes for their compatible cross-game faction battles, rather than expecting three entirely unrelated systems.',
1565670:'An under-the-radar single-player-first RTS with substantial fleet and base management. Its five factions and campaign emphasis make it a worthwhile C&C-shaped detour into space.',
1934720:'A newer, explicitly C&C-inspired prospect with two sides and AI skirmish. Still Early Access: inspect what is playable now rather than buying it for a promised finished campaign.',
1031730:'A retro construction-and-warfare RTS to investigate for the C&C lineage. Early Access and mixed reception make it an experimental pick, not a safer recommendation than Tempest Rising.',
2088550:'A visually distinctive retro RTS for the original C&C and pixel-art itch. Treat the current Early Access build and available missions as the product, not the eventual roadmap.',
2583660:'A watchlist candidate for faction-led sci-fi base building. It is not a released recommendation; videos show development, not proof of a finished purchasable game.',
908770:'A particularly relevant watchlist entry for the Generals-style modern-war feeling. Keep it separate from playable games until an actual release is confirmed.',
2388620:'A very promising-looking old-school RTS with striking industrial factions and detailed pixel artwork. It is an upcoming project, not something this catalog claims you can buy and play today.',
2610770:'Worth tracking for its bleak industrial warfare and unusual presentation. This is an upcoming discovery, with advertised systems kept distinct from verified released features.',
5265230:'A very recent, very small-audience C&C-style discovery. Two negative reviews are not enough for a definitive verdict, but they are enough to withhold a strong recommendation. Investigate carefully.',
1072190:'A recognizable faction-and-base RTS from a familiar multiplayer setting. The concept fits, but weak player reception makes this a sale/demo-level investigation rather than a top buy.',
686260:'The attraction is configuring your own army instead of accepting fixed faction arsenals. Reception is weak, so consider the customization idea rather than assuming it is the most polished C&C successor.',
290790:'Three sharply different factions are the draw, especially the unusual Goo economy. A distinctive RTS to investigate despite mixed reception; not simply Generals with a different coat of paint.',
245370:'An older sci-fi RTS with faction and territory ideas worth looking at. Poor reception makes it a curiosity for genre collectors, not an essential recommendation.',
2710:'One of the strongest older alternatives for the modern-military, resource-and-base-building loop. Expect a dated presentation and check current compatibility, but the connection to Generals is much closer than most tactical wargames.',
9760:'The expanded Act of War experience, with additional units and scenarios. A good companion to Direct Action, though this is a classic edition rather than a new release.',
530040:'A smaller old-school construction RTS that aims directly at the classic formula. Mixed reception means it belongs in the deep-cut shelf, behind the stronger recommendations.',
1841630:'A niche combined-arms base builder with a very small and weak review sample. Included as a clearly cautioned discovery, not as a hidden masterpiece.',
1114830:'A small-scale indie take on modern military RTS. Check the current limitations and player feedback before paying; the hardware fantasy fits better than the overall reception.',
2732960:'The reference point: specialized generals, supply-line raids, memorable factions and the enormous mod scene. Keep the original installed alongside your preferred overhauls rather than treating it as obsolete.',
2229870:'The original Generals campaigns and faction foundations. Zero Hour is the deeper skirmish/mod platform, but this remains worthwhile for the original missions and pacing.',
2229850:'An essential C&C branch with wonderfully excessive faction identities. Yuri\'s Revenge expands the toy box, and it is the required foundation for Mental Omega.',
17480:'The colorful naval-and-land counterpart to Generals, with an emphasis on faction abilities and cooperative campaign play. It is also the base game required by Generals Evolution.',
24800:'A single-player-focused Red Alert 3 companion with challenge scenarios and extra units. Do not buy it expecting the base game\'s multiplayer or as a replacement for Red Alert 3 when installing its mods.',
24790:'A strong transition from Generals to futuristic C&C, with a substantial campaign and the familiar harvest-build-attack rhythm. A particularly safe classic to investigate.',
24810:'The faction-specialization recommendation for Tiberium Wars fans. Its subfactions make it especially relevant when the different generals are what you love about Zero Hour.',
1213210:'The original C&C and Red Alert foundations with modern presentation and convenience. A classic remaster collection, not a recreation of Generals\' 3D warfare.',
2229880:'Atmospheric, asymmetric futuristic C&C with the Firestorm expansion. Choose it for the setting and classic campaigns, then explore its separate standalone community projects.',
9420:'My strongest large-battle detour: sprawling economies, land/air/naval warfare and spectacular experimental units. Forged Alliance Forever is a separate community enhancement worth investigating for improved AI and co-op.',
40100:'A streamlined, more immediately accessible Supreme Commander. Easier to get moving than Forged Alliance, but not a substitute for the latter\'s enormous simulation and mod ecosystem.',
298030:'The classic foundation for economy-heavy, mass-army RTS. Its streaming economy and scale are the relevant connection, rather than modern-military realism.',
386070:'A spectacular step beyond flat battlefields into warfare across planets. Best when scale and escalating destruction matter more than a cinematic story campaign.',
507490:'A large-army sci-fi strategy choice for battles that keep growing. The mixed reception and different macro emphasis warrant checking gameplay before choosing it over Forged Alliance or BAR.',
1796720:'Factory-building and army production make an intriguing combination, but current reception is very poor. Keep it as a cautious Early Access experiment, not a top recommendation.',
1699050:'An upcoming large-scale RTS to track for the Supreme Commander feeling. Advertised scale and factions are development promises until a playable release is confirmed.',
334920:'A very strong free RTS with flexible construction and a deep unit roster. A meaningful alternative to paid large-scale games, not just a technology demo.',
647960:'One of the best lightweight, moddable skirmish choices. The simple visuals hide a surprisingly substantial RTS, especially when you want big maps without demanding hardware.',
303860:'A compact, less-known army-and-base builder. A useful lightweight discovery, with a much smaller player sample than the genre\'s established favorites.',
3213120:'A fresh sci-fi RTS discovery with a small but encouraging audience. A good title to inspect after the obvious C&C successors, while keeping review confidence in proportion.',
1241950:'A free classic centered on designing vehicles and developing a persistent war machine. Use its official project as well as the Steam listing, and do not mistake the Steam date for the original game\'s age.',
253880:'An ambitious classic with construction, customizable forces and unusual battlefield systems. Expect an older interface and check modern-system behavior before committing to a long campaign.',
1900:'An unusual faction-driven classic whose armies do not all build and operate the same way. Worth revisiting for asymmetry, with dated controls and compatibility in mind.',
1292180:'A post-apocalyptic C&C-era rediscovery with three distinct sides. Recent maintenance does not make it a new game, but it is useful for scratching the old-school skirmish itch.',
1292170:'A deliberately rough-edged post-apocalyptic classic. Best approached as a C&C-era curiosity with personality, not as a modern RTS replacement.',
289440:'A genuinely unusual older RTS with terrain shaping and transformative units. This is a creative mechanical detour rather than the closest match to Generals.',
3556750:'The definitive-era package for a classic faction RTS with enormous personality. A particularly good choice for base construction and brutal sci-fi armies; distinguish this edition from older mod-specific builds.',
826630:'Dieselpunk mechs and cover-based warfare are the draw. Its sector-control battles differ from the freely expanding economy of Zero Hour, and player reception is mixed.',
1202130:'A strong campaign-focused RTS about holding lines against alien swarms. Its constrained construction and mission design are not an open-ended Generals-style base-building sandbox.',
459220:'An accessible army builder with a substantial campaign and recognizable Halo units. Fixed base plots make it simpler and more constrained than Zero Hour.',
777770:'A dinosaur-and-fantasy-themed traditional RTS. The theme is appealing, but mixed reception keeps it behind the stronger fantasy recommendations.',
896250:'A newer fantasy/sci-fi RTS discovery with encouraging but still limited Early Access feedback. Watch actual current gameplay, not just the advertised long-term ambition.',
1328990:'A particularly promising fantasy RTS for players who want heroes and base building without abandoning classic strategy structure. Still Early Access, despite strong reception.',
1466860:'A polished historical alternative with economy, defenses, armies and distinct civilizations. A different military era, but a strong fit for the satisfaction of constructing a war machine.',
813780:'A deeply established, content-rich base-building RTS. Less like modern military hardware, but an excellent long-term home for campaigns, skirmish and varied civilizations.',
933110:'A strong choice when you want historical warfare to include gunpowder, artillery and asymmetric civilizations. Check the edition\'s current content rather than treating it as a new release.',
1934680:'A great bridge from conventional armies to myth units and spectacular god powers. The base-building foundation remains familiar even when the battlefield becomes fantastical.',
287450:'A very replayable historical RTS that advances through eras within a larger territorial game. More civilization-scale than Zero Hour, but excellent for building toward overwhelming armies.',
254760:'A classic multi-era RTS newly available in this store edition. Its 2026 listing date is a reissue date, not evidence of a newly developed game.',
254780:'The second Empire Earth remains a sprawling classic rather than a modern release. Investigate for eras, nations and large conflicts, with older-system compatibility in mind.',
311290:'The most substantial RPG/RTS hybrid detour here. Play it for campaign characters and base-building battles, not for an exact imitation of modern military skirmish.',
817540:'A standalone SpellForce 3 expansion for players who want story-heavy RPG progression alongside real-time army command. It does not require treating the base campaign as the same game.',
1154040:'A particularly appealing standalone fantasy campaign with RTS battles. A good choice for a memorable single-player journey rather than endless modern-war skirmishes.',
946660:'An affordable old-school fantasy RTS with clear Warcraft-era inspiration. A useful hidden-gem candidate when compact campaigns and classic controls sound appealing.',
433280:'Persistent heroes and many fantasy races give this classic unusual long-term build variety. Expect old-school compatibility and interface compromises.',
333420:'A historical mass-army choice for large infantry formations and economy building. Much closer to the giant-battle fantasy than to Zero Hour\'s specialized modern units.',
2012510:'A modern faction RTS with substantial negative reception. Included so the collection is informative, but not recommended ahead of the better-reviewed alternatives.',
2921580:'An upcoming fantasy/sci-fi competitive RTS worth tracking, not a confirmed released alternative. Check public access separately from a Steam wishlist page.',
1762570:'A recently released fleet-command detour with a different pace from ground RTS. Worth investigating for space warfare rather than assuming it replaces ground-base construction.',
244160:'A beautifully distinctive fleet RTS collection built around three-dimensional battles and a mobile mothership. A great strategic detour, not a ground-base-building equivalent.',
281610:'A strong single-player RTS with a mobile land carrier and desert warfare. Its setting and combined arms may appeal even though conventional construction is constrained.',
1840080:'A modern Homeworld sequel with very poor reception. Keep it as a heavily cautioned option; the remastered classics and Deserts of Kharak are safer starting points.',
1575940:'A compelling large-scale real-time space strategy game with orbital development and fleet warfare. More empire management than a short C&C skirmish.',
204880:'An established real-time space-empire classic with extensive replayability. Its scale and economy are the connection; conventional ground bases are not.',
32470:'A durable Star Wars strategy foundation with both space and ground battles and a major mod scene. Construction is more constrained than C&C, particularly in tactical battles.',
573410:'An outstanding asymmetric challenge against an AI empire. The appeal is planning a war against an overwhelming opponent rather than mirrored faction duels.',
40400:'The original AI War is a demanding strategic puzzle at enormous scale. Best for players who enjoy learning complex systems, not for a casual Zero Hour reskin.',
1113030:'An indie fleet RTS with space-base construction and modular fleets. A promising niche choice, but still Early Access and smaller in audience than Homeworld or Sins.',
887570:'Detailed fleet construction and tactical naval-style space combat. There is no normal base-building economy, so treat it as a tactical neighbor.',
1677280:'A sector-control WWII RTS with base upgrades and tactical combat. Mixed reception matters, and its battlefield economy differs from free-form C&C construction.',
231430:'A substantial WWII tactical RTS with faction bases, squads and territorial control. Good for intense engagements, but not the same economic sandbox as Zero Hour.',
1611600:'Large modern-war battles with detailed combined arms and a tactical deployment system. No conventional base-building economy: pick it for military tactics, not construction.',
1604270:'An ambitious modern-military tactical game with mixed reception. Its units may match the fantasy, but it does not offer the ordinary C&C base-building loop.',
251060:'One of the strongest modern-military tactical detours for an enormous unit roster. Command forces and logistics rather than constructing a traditional RTS base.',
1109680:'A particularly sensible single-player-focused tactical-war choice. It trades base building for battlefield command, making the distinction important before buying.',
1839950:'A hard-edged campaign and tactical combat recommendation. Limited resources and unit preservation are central; a conventional freely constructed base is not.',
1128860:'A WWII tactical option for detailed units and battlefield interaction. Mixed reception and the absence of normal base building keep it outside the closest-match shelf.',
400750:'Detailed WWII warfare with direct unit control and realistic tactical stakes. A strong neighbor for military enthusiasts, not a C&C-style construction game.',
463530:'An excellent unusual RTS about building an ant colony and fielding armies. The theme is radically different, but the growth-and-war loop is genuinely relevant.',
923100:'An inventive RTS where organisms grow into functional fighting machines. A strong experimental discovery rather than a conventional faction-base clone.',
1309610:'A smart alternative for lower-micro command: draw operational orders while managing territory and production. Current official metadata explicitly includes AI opponents and co-op against them.',
2239150:'A compact, highly regarded defense-and-economy game. Great for short strategic sessions, but not an enemy-base skirmish RTS.',
1272320:'A particularly satisfying fortification-and-army defense game. Build a town and survive huge assaults, rather than expecting symmetric faction warfare.',
1422440:'A creative fortress-building and defense RTS. Its architectural construction is the draw, and its survival structure is distinct from classic C&C matches.',
644930:'A classic survival RTS for building a fortified colony against overwhelming hordes. No enemy-base economy or Generals-style opposing faction production.',
1426450:'A dark-fantasy survival alternative with large enemy swarms. Worth investigating for defense and escalation, while keeping its mixed reception in view.',
3052730:'A new survival-RTS discovery to inspect for fortified settlements and swarm pressure. Early Access means the current playable offering matters more than the roadmap.',
3010280:'A very new, small-audience RTS experiment with skirmish in its official feature set. Promising enough to inspect, but not yet an established must-buy.',
1996600:'An inventive tiny RTS built around networked structures and expansion rather than ordinary unit armies. Excellent as a mechanical detour, not the closest match to Zero Hour.',
286000:'A compact controller-friendly RTS with animal armies and quick decisions. A good contrast to heavyweight military simulations and long base-building matches.',
2745870:'A nostalgic side-view tactical warfare collection. Clearly separated from full base-building RTS so it does not inflate the close-match recommendations.',
2599770:'A niche modern RTS with both base construction and a separate no-base tactical mode. The fit is relevant, but mixed feedback makes it a cautious discovery.',
1527070:'A small Early Access modern-war RTS with very poor feedback and limited currently described content. Investigate development health before spending; not a strong recommendation.',
21970:'An interesting classic that combines deception, military production and WWII warfare. More directly relevant to base-building fans than many modern tactical wargames.'
}
ORIGINAL={2710:2005,9760:2006,2732960:2003,2229870:2003,2229850:2000,17480:2008,24800:2009,24790:2007,24810:2008,2229880:1999,9420:2007,298030:1997,1241950:1999,253880:2000,1900:2005,1292180:1998,1292170:1997,289440:2004,254760:2001,254780:2005,433280:2004,32470:2006}
# Reviewed classic modes, separate from developer-advertised upcoming modes.
AI_CLASSICS={2732960,2229870,2229850,17480,24790,24810,1213210,2229880,9420,40100,298030,647960,303860,1241950,1292180,1292170,289440,3556750,459220,813780,1934680,287450,254760,254780,433280,333420,244160,281610,1575940,204880,32470,251060,231430,21970}
NO_BASE={1611600,1604270,251060,1109680,1839950,1128860,400750,887570,2745870}
BASE_SPECIAL={1677280:'Headquarters and sector-control construction',231430:'Headquarters and sector-control construction',1202130:'Limited mission/base construction',459220:'Fixed base plots',244160:'Mobile mothership and fleet production',281610:'Mobile carrier; not conventional base construction',1840080:'Mothership and fleet production',1762570:'Fleet-focused; no conventional ground bases',1575940:'Orbital structures and empire development',204880:'Orbital structures and empire development',32470:'Galactic development and fixed tactical build pads',573410:'Space structures and asymmetric empire warfare',40400:'Space structures and asymmetric empire warfare',923100:'Grow living organisms instead of normal bases',1996600:'Capture/build a network; no conventional armies',463530:'Underground colony construction',2239150:'Compact town construction and wave defense'}
EXTRA_LINKS={9420:[{'provider':'FAF community','url':'https://www.faforever.com/play','kind':'project','verified':True,'sourceUrl':'https://www.faforever.com/play','evidence':'Community enhancement; requires ownership of Forged Alliance.'},{'provider':'GOG','url':'https://www.gog.com/en/game/supreme_commander_gold_edition','kind':'store','label':'GOG Gold Edition bundle','verified':True,'sourceUrl':'https://www.faforever.com/play','evidence':'Official FAF installation guide identifies Steam and GOG editions.'}],1241950:[{'provider':'Official site','url':'https://wz2100.net/','kind':'project','verified':True,'evidence':'Official Warzone 2100 project.'}]}
def main():
    steam=json.loads((ROOT/'data/rts-steam.json').read_text())['items'];external=json.loads((ROOT/'data/rts-external.json').read_text())['items'];out={}
    for g in steam:
        aid=g['appid'];about=g.get('rtsEvidence',{}).get('about','');tags=['RTS'];up=g.get('comingSoon')
        base='Construction and production economy'
        if aid in NO_BASE:base='No conventional base-building economy';tags.append('Tactical neighbor')
        elif aid in BASE_SPECIAL:base=BASE_SPECIAL[aid]
        elif g['collection']=='Survival & defense RTS':base='Settlement/fortress construction and wave defense';tags.append('Survival defense')
        if g['collection'] in ['C&C-style base builders','Command & Conquer lineage'] or aid in [21970]:tags.append('Zero Hour-like')
        if aid not in NO_BASE and aid not in BASE_SPECIAL:tags.append('Base building')
        skirmish='Not confirmed by the current source; do not assume absence'
        if up:skirmish='Upcoming; advertised modes are not released features'
        elif aid in AI_CLASSICS or re.search(r'\bskirmish\b|\bAI (?:opponents|players|enemies)\b|against.{0,25}\bAI\b',about,re.I):skirmish='Yes / skirmish or AI opponents documented';tags.append('AI skirmish')
        elif g['collection']=='Survival & defense RTS':skirmish='Solo survival / defense, not symmetric skirmish'
        if aid==24800:skirmish='Single-player AI skirmish, campaigns and Commanders Challenge; no multiplayer';tags.append('AI skirmish')
        o={'curatorWhy':WHY.get(aid,g['summary']),'rtsInfo':{'baseBuilding':base,'skirmish':skirmish,'sourceUrl':g['steamUrl']},'tags':tags}
        if aid in ORIGINAL:o['originalReleaseYear']=ORIGINAL[aid];o['releaseNote']='The sortable store date identifies this edition/listing; the original game is older.'
        if g.get('rating') is not None and g['rating']<70:o['recommendationCaution']='Reception is mixed or poor. This is a cautious discovery, not a top buy.'
        if g.get('reviewCount',0)<100:o['confidence']='Exploratory';o['recommendationCaution']='Small review sample: treat this as a discovery to inspect, not a proven hit.'
        if aid==5265230:o['fit']=5;o['recommendationCaution']='Very new and only two reviews, both negative. No strong recommendation is justified.'
        if aid in [1527070,1796720,245370,1840080]:o['fit']=5
        if up:o['fit']=None;o['prospectiveFit']=g['fit'];o['recommendationCaution']='Watchlist only: no current purchase recommendation for an unreleased game.'
        if not up and (g.get('releaseDate') or '')[:4] in ['2025','2026'] and o.get('originalReleaseYear',2026)>=2025:o['tags']=sorted(set(o['tags']+['Recent RTS release']))
        if aid in EXTRA_LINKS:o['storefronts']=EXTRA_LINKS[aid]
        if aid==9420:o['requirements']='Forged Alliance Forever is an optional community client, not a free license for the game. Its current setup requires linking an owned Steam or GOG copy.'
        out[g['id']]=o
    for g in external:
        tags=['RTS','Base building'];base='Construction and production economy';skirmish='See the exact project mode list'
        if g['collection'] in ['Zero Hour mods & overhauls','C&C mods & total conversions','C&C community standalones']:tags.append('Zero Hour-like')
        if g['kind']=='Mod / total conversion':tags.append('RTS mod')
        if g['id']!='external:world-in-conflict':tags.append('AI skirmish');skirmish='AI/skirmish available in the project or required base game'
        else:base='No conventional base-building economy';skirmish='Tactical campaign; not a base-building skirmish';tags=['RTS','Tactical neighbor']
        if g['id']=='external:warcraft-1-remastered':skirmish='Single-player campaign; check the remaster mode list';tags=[x for x in tags if x!='AI skirmish']
        o={'rtsInfo':{'baseBuilding':base,'skirmish':skirmish,'sourceUrl':g['primaryUrl']},'tags':tags}
        if g.get('releaseYear'):o['originalReleaseYear']=g['releaseYear']
        out[g['id']]=o
    target=ROOT/'data/rts-curation.json';target.write_text(json.dumps({'schemaVersion':1,'generatedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'Editorial fit is not a critic score. Store reception and small samples constrain recommendations. Upcoming entries are not purchase recommendations.','overrides':out},ensure_ascii=False,indent=2)+'\n')
    print('Curated',len(out),'RTS identities')
if __name__=='__main__':main()
