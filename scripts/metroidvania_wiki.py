"""Native Metroidvania pages generated from the same interactive snapshot."""
from catalog_model import game_key,score
HUB='Metroidvanias'
def build(root,catalog):
 from wiki_builder import table,media_atlas,link,rank,m
 out=root/'wiki';rows=[g for g in catalog['items'] if HUB in g.get('hubs',[])]
 if not rows:return
 text='# Metroidvanias: every locked door is a promise\n\n'
 text+='**[Open the interactive collection]('+link({'hub':HUB})+')** | [Every game: images and videos](Metroidvania-Media) | [Free games and creator discoveries](Metroidvania-Underground) | [Portable HTML](https://github.com/Herbertofury/Games/releases/latest)\n\n'
 text+=f'**{len(rows)} unique entries.** Traditional worlds, dark castles, movement playgrounds, puzzle labyrinths and clearly labelled adjacent games. Official store dates are not automatically original release dates.\n\n'
 picks=sorted([g for g in rows if not g.get('comingSoon') and (score(g) or 0)>=9],key=rank)
 text+='## Start here\n\n'+media_atlas(picks[:12],HUB)
 text+='## Choose your rabbit hole\n\n| Shelf | What you get |\n|:--|:--|\n'
 shelves=[('Core Metroidvanias',{'tag':'MV core'},'Ability-led world exploration, with adjacent formats kept separate.'),('Recent releases',{'tag':'Recent Metroidvania release','playable':'true','sort':'newest'},'Verified 2025-2026 releases, not old games relabelled by a patch.'),('Under the radar',{'hidden':'true'},'Smaller-audience discoveries with rating counts visible.'),('Free mini-vanias',{'free':'true','playable':'true'},'Creator freeware and browser worlds, including short jam projects.'),('3D worlds',{'tag':'MV 3D'},'First-person and third-person exploration.'),('Playable demos',{'demo':'true'},'Demo editions attached to their actual game, not counted twice.'),('Watchlist',{'status':'Upcoming'},'Unreleased full games, explicitly separated.')]
 for label,params,note in shelves:text+=f'| [{label}]({link(dict(hub=HUB,**params))}) | {note} |\n'
 text+='\n## Fresh discoveries\n\n'+table(sorted([g for g in rows if 'Recent Metroidvania release' in g['tags']],key=lambda x:x.get('releaseDate') or '',reverse=True))
 text+='\n## The complete collection\n\n'
 for col in sorted({g.get('metroidvaniaCollection',g['collection']) for g in rows}):text+='### '+col+'\n\n'+table(sorted([g for g in rows if g.get('metroidvaniaCollection',g['collection'])==col],key=rank))
 text+='\n## Watchlist, not released full games\n\n'+table(sorted([g for g in rows if g.get('comingSoon')],key=rank))
 text+='\n[Scoring and sources](Ratings-and-Sources). Editorial fit is not a claim of hands-on testing. Every confirmed source is linked on the individual game page.\n'
 (out/'Metroidvanias.md').write_text(text)
 (out/'Metroidvania-Media.md').write_text('# Metroidvanias: the complete media atlas\n\n'+f'**{len(rows)} entries**, each with artwork, exact video sources and confirmed distribution links. The wiki renders artwork and links videos; the interactive library provides in-page players.\n\n[Recommendations](Metroidvanias) | [Interactive players]('+link({'hub':HUB})+') | [Portable HTML](https://github.com/Herbertofury/Games/releases/latest)\n\n'+media_atlas(rows,HUB))
 underground=[g for g in rows if not g.get('steamUrl') or any(s['provider']=='itch.io' or s.get('kind')=='support' for s in g.get('storefronts',[]))]
 (out/'Metroidvania-Underground.md').write_text('# Beyond the usual storefronts\n\nCreator games, freeware, browser mini-vanias, documented demo editions, and support pages. A jam game, an unfinished prototype and a commercial full release are not the same thing. Native itch.io scores keep their own scale and sample sizes.\n\n[Back to the full collection](Metroidvanias)\n\n'+media_atlas(underground,HUB))
 home=(out/'Home.md').read_text().replace('# A home for every great discovery','# A home for every great discovery\n\n**NEW: [Metroidvanias](Metroidvanias) | [Full visual atlas](Metroidvania-Media) | [Creator discoveries](Metroidvania-Underground)**').replace('Cross-genre games appear',f'{len(rows)} in Metroidvanias. Cross-genre games appear');(out/'Home.md').write_text(home)
 p=out/'_Sidebar.md';p.write_text(p.read_text().replace('- [Home](Home)','- [Home](Home)\n- [Metroidvanias](Metroidvanias)\n- [Every Metroidvania: media atlas](Metroidvania-Media)\n- [Metroidvania underground](Metroidvania-Underground)'))
 for g in rows:
  p=out/(game_key(g)+'.md');s=p.read_text();s=s.replace('[Roguelites](Roguelites)','[Metroidvanias](Metroidvanias)') if g.get('hubs')==[HUB] else s+'\n[Also in Metroidvanias](Metroidvanias)\n'
  info=g.get('metroidvaniaInfo',{});s+='\n## Explorer\'s brief\n\n**Structure:** '+m(info.get('structure'))+'\n\n**Store-described mechanics:** '+m(info.get('traversal'))+'\n\n'+m(info.get('basis'))+'\n'
  if g.get('aliases'):s+='\n**Also find this entry by:** '+m(', '.join(g['aliases']))+'\n'
  p.write_text(s)
