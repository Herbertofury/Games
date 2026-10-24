"""Couch party atlas and mode-specific local-player navigation from one snapshot."""
import collections,copy,json
from catalog_model import game_key
HUB='Couch co-op & party'
def count_text(xs):
 xs=sorted(set(xs or []))
 if not xs:return 'Count needs confirmation'
 if len(xs)==1:return str(xs[0])
 return str(xs[0])+'-'+str(xs[-1]) if xs==list(range(xs[0],xs[-1]+1)) else ' or '.join(map(str,xs))
def build(root,catalog):
 from wiki_builder import link,rank,m,media_atlas
 out=root/'wiki';rows=[copy.deepcopy(g) for g in catalog['items'] if HUB in g.get('hubs',[])]
 if not rows:return
 for g in rows:g.update(collection=g['partyCollection'],fit=g['partyFit'])
 rows.sort(key=rank)
 def grid(gs):
  text='| Game | Local people | Co-op / versus | Setup / edition | Recommendation |\n|:--|:--|:--|:--|:--|\n'
  from catalog_model import score
  for g in gs:
   p=g['partyInfo'];summary='; '.join(t+': '+count_text(p['coopCounts'] if t=='Co-op' else p['versusCounts']) for t in p['modes']);notes='; some capacity requires DLC' if any(x.get('requiresDlc') for x in p['modesDetail']) else ''
   text+=f"| [{m(g['name'])}]({game_key(g)}) | {count_text(p['playerCounts'])}{notes} | {m(summary)} | {m(p['participation'])}; {m(p['platform'])} | {str(score(g))+' / 10' if score(g)!=None else 'Watchlist'} |\n"
  return text+'\n'
 def matched(n,mode=''):
  return [g for g in rows if not g.get('comingSoon') and any(n in md['counts'] and (not mode or md['type']==mode) for md in g['partyInfo']['modesDetail'])]
 text='# Couch co-op & party: one more round\n\n'
 text+='**[Open the interactive party lobby]('+link({'hub':HUB})+')** | [Every game: artwork and videos](Party-Media) | [Player-count guide](Party-Player-Guide) | [Portable app](https://github.com/Herbertofury/Games/releases/latest)\n\n'
 text+=f"**{len(rows)} unique games and projects.** Built around Disc Jam, Lethal League and Blaze, Thunder Rally, Hyper Jam, and Boomerang Fu. Their shared appeal is fast, readable, competitive local play; cooperative adventures have a separate route.\n\n"
 text+='## Your kind of chaos\n\n'+media_atlas([g for g in rows if g['partyCollection']=='Your favorites & closest matches'][:16],HUB)
 text+='## How many people are coming?\n\n| Route | Why it matters |\n|:--|:--|\n'
 for title,params,note in [('Two-person teamwork',{'partyPlayers':'2','partyMode':'Co-op','partySetup':'simultaneous','playable':'true'},'Cooperative modes that actually fit two people.'),('Four local players',{'partyPlayers':'4','partySetup':'simultaneous','playable':'true'},'Four participants on the same system, not four online.'),('Five or more',{'partyPlayers':'5plus','partySetup':'simultaneous','playable':'true'},'Big-couch games; device limitations remain visible.'),('Phone-controlled parties',{'partySetup':'phones','playable':'true'},'One host screen, personal devices; audience slots are not players.'),('Fresh party releases',{'tag':'Recent couch release','playable':'true','sort':'newest'},'Source-dated recent releases, with reception and sample sizes visible.'),('Upcoming games',{'status':'Upcoming'},'Watchlist entries, not finished releases.')]:text+=f'| [{title}]({link(dict(hub=HUB,**params))}) | {note} |\n'
 text+='\n[Two-player guide](Party-Two-Players) | [Four-player guide](Party-Four-Players) | [Five-plus guide](Party-Five-Plus)\n\n## All collections\n\n'
 for col in sorted({g['partyCollection'] for g in rows}):text+='### '+col+'\n\n'+grid([g for g in rows if g['partyCollection']==col])
 text+='## Honest boundaries\n\nLocal multiplayer is not automatically co-op, and a Steam Co-op tag can describe a team-versus format. Counts are tied to the recorded edition and mode. Separate online, wireless, spectator and tournament numbers do not expand same-device capacity. Unknown numerical limits remain visible as unknown and are excluded from exact-player filters. Source links, conditions, and evidence are on every game page.\n'
 (out/'Couch-Coop-and-Party.md').write_text(text)
 (out/'Party-Media.md').write_text(f'# Couch parties: the complete visual atlas\n\n**{len(rows)} entries**, all with real artwork, supported embedded-video metadata and direct source links. Official trailers, community footage and short creator loops are separately credited. The wiki displays artwork and links videos; the portable HTML provides the players.\n\n[Party home](Couch-Coop-and-Party) | [Interactive lobby]('+link({'hub':HUB})+')\n\n'+media_atlas(rows,HUB))
 for n,title,slug in [(2,'Two-person teamwork and rivalries','Party-Two-Players'),(4,'Four people, one system','Party-Four-Players')]:
  (out/(slug+'.md')).write_text('# '+title+'\n\n[Party home](Couch-Coop-and-Party) | [Mode and controller guide](Party-Player-Guide)\n\nCounts match an actual local mode. Some entries include an optional DLC mode; read the individual conditions.\n\n## Work together\n\n'+grid(matched(n,'Co-op'))+'## Face off\n\n'+grid(matched(n,'Versus')))
 (out/'Party-Five-Plus.md').write_text('# A bigger game night\n\n[Party home](Couch-Coop-and-Party)\n\nFive or more local participants in a documented mode. Phone, shared-controller, hotseat and VR setups are not interchangeable with five gamepads.\n\n'+grid([g for g in rows if not g.get('comingSoon') and any(n>=5 for n in g['partyInfo']['playerCounts'])]))
 (out/'Party-Player-Guide.md').write_text('''# Read the room: local-player guide

[Party home](Couch-Coop-and-Party) | [Complete media atlas](Party-Media)

## People, not connection slots

The interactive lobby intersects headcount with the **same local mode**. A game with two-person co-op and four-person versus does not qualify as four-person co-op. Team-versus is competitive, not a cooperative story campaign. Numeric caps are not borrowed from an online lobby or console version without an explicit edition note.

**Simultaneous:** multiple people playing on the same device with shared- or split-screen play. Input requirements vary.

**Phone controllers:** one host screen and web-enabled devices. Expect connectivity requirements. Jackbox game minimums differ inside a pack; an audience of thousands is not thousands of active players.

**Hotseat:** pass a controller or alternate turns. This is not simultaneous gamepad play.

**Asymmetric:** additional hardware or information roles, such as a VR tree and phone-controlled squirrels, or a bomb operator and manual readers.

## Conditions that change the answer

TowerFall has two-person Quest co-op in the base game and up-to-four cooperative play with Dark World. BattleBlock Theater's story and arena have different counts. Disc Jam singles and doubles are two or four human configurations. Nintendo local wireless means multiple systems, not more people on a single console. Optional DLC capacities can be excluded with the lobby checkbox.

More than four controllers may need a compatible input backend, device mix, or shared-controller scheme. A maximum headcount is not a guarantee that any arbitrary pile of controllers will work. Mode-specific setup notes and evidence links are retained in each game's dossier.

## Recommendation and release dates

Editorial fit emphasizes your fast-round favorites without disguising weaker reception. Ratings retain their original provider and review count. A tiny positive sample is not the same evidence as years of strong reception. Full games, Early Access, demos, prototypes, upcoming titles and archived store pages are distinct. Remote Play Together can stream an existing local mode but does not create more native local slots.

## Refresh

The repository stores canonical source facts, curated modes, exact media, and unresolved candidates separately. Manual refresh preserves reviewed overrides and stable game IDs. There is no scheduled crawler. Confirmed stores are the researched set, not a claim to every key reseller worldwide.
''')
 for g in rows:
  p=out/(game_key(g)+'.md');text=p.read_text();info=g['partyInfo'];text+='\n## Game-night dossier\n\n[Back to couch co-op & party](Couch-Coop-and-Party)\n\n**Edition:** '+m(info['platform'])+'\n\n**Participation:** '+m(info['participation'])+'\n\n**Input setup:** '+m(info.get('inputs'))+'\n\n| Local mode | People | Conditions | Count source |\n|:--|:--|:--|:--|\n'
  for md in info['modesDetail']:text+=f"| {m(md['name'])} ({m(md['type'])}) | {count_text(md['counts'])} | {m(md.get('notes')) or 'See input setup'} | [Evidence]({md['sourceUrl']}) |\n"
  text+='\n'+m(info.get('notes'))+'\n\n'+m(info['basis'])+'\n';p.write_text(text)
 home=out/'Home.md';home.write_text(home.read_text().replace('# A home for every great discovery','# A home for every great discovery\n\n**NEW: [Couch co-op & party](Couch-Coop-and-Party) | [Two people](Party-Two-Players) | [Four people](Party-Four-Players) | [Five or more](Party-Five-Plus)**',1))
 sidebar=out/'_Sidebar.md';sidebar.write_text(sidebar.read_text().replace('- [Home](Home)','- [Home](Home)\n- [Couch co-op & party](Couch-Coop-and-Party)\n- [Party: full media atlas](Party-Media)\n- [Two people](Party-Two-Players)\n- [Four people](Party-Four-Players)\n- [Five or more](Party-Five-Plus)\n- [Player-count guide](Party-Player-Guide)',1))
