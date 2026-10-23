"""Deterministic editorial layer; provider facts and personal ratings stay separate."""
import json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[1]
rows=json.loads((R/'data/metroidvania-steam.json').read_text())['items']+json.loads((R/'data/metroidvania-external.json').read_text())['items']
def key(s):return re.sub('[^a-z0-9]','',s.lower())
by={key(g['name']):g for g in rows};overrides={}
def setgame(name,**fields):
 g=by.get(key(name))
 if g:overrides.setdefault(g['id'],{}).update(fields)
 return g
reasons={
'Hollow Knight':('A sprawling, atmospheric benchmark: meaningful movement upgrades, memorable boss fights and a world that rewards curiosity long after the obvious route ends.',10),
'Hollow Knight: Silksong':('For the top of the exploration queue: fluid movement, a strong sense of place and demanding encounters. Compare its current player reception and gameplay before choosing it as your first entry.',10),
'Ori and the Will of the Wisps':('The movement-first showcase: a luminous world, expressive traversal and a less equipment-heavy approach than the Castlevania branch.',10),
'Bloodstained: Ritual of the Night':('One of the most direct fits for Symphony of the Night fans: equipment, loot, collectible powers and a gothic castle to gradually unravel.',10),
'Castlevania Advance Collection':('The official bundle for Circle of the Moon, Harmony of Dissonance and Aria of Sorrow. Excellent for exploring the equipment-and-ability side of the genre; Dracula X is the separate stage-based extra.',10),
'Castlevania Dominus Collection':('The official bundle for Dawn of Sorrow, Portrait of Ruin and Order of Ecclesia, with their distinct combat systems and castle exploration. The Haunted Castle extras are not Metroidvanias.',10),
'Nine Sols':('Prioritize this for deliberate parry combat and demanding bosses. Its combat rhythm is a better reason to choose it than expecting a relaxed sightseeing adventure.',10),
'Prince of Persia The Lost Crown':('A strong movement-and-combat choice, with an especially appealing mix of precision platforming, time-themed abilities and navigation tools.',10),
'Blasphemous 2':('A strong dark-fantasy pick for grotesque religious imagery, interconnected exploration and a more traversal-driven structure than a simple stage-based action game.',9),
'ENDER MAGNOLIA: Bloom in the Mist':('A good next stop for atmospheric dark fantasy, companion-driven combat and build choices without losing the exploration emphasis.',9),
'GRIME':('Choose this for unusual organic environments, deliberate fights and a distinctive absorption-based identity rather than familiar castle corridors.',9),
'Environmental Station Alpha':('A tiny-looking but substantial science-fiction labyrinth. Especially rewarding for players who enjoy secrets and do not need lavish presentation.',9),
'ANIMAL WELL':('The puzzle-first essential: knowledge, observation and the unexpected uses of your tools matter more than combat statistics. Best explored with minimal spoilers.',10),
'La-Mulana':('An archaeological puzzle labyrinth for players who enjoy taking notes and solving opaque mysteries. This is intentionally not the easy first recommendation.',9),
'La-Mulana 2':('A deep puzzle-and-exploration sequel for players who actively enjoy deciphering clues. Bring curiosity and patience rather than expecting a straightforward action route.',9),
'Astalon: Tears of the Earth':('A compact-looking tower with layered routes and character switching. A strong pick for the exploration puzzle of reconnecting a hostile place.',9),
'Phoenotopia: Awakening':('A broad adventure with puzzles, towns, combat and exploration. More of an action-adventure hybrid than a pure combat gauntlet.',9),
'Islets':('An approachable, charming choice when you want interconnected discovery without committing to the genre\'s harshest difficulty spikes.',9),
'Shee po':('Transformation-led traversal rather than standard weapon combat.',8),
'Well Dweller':('A recent, storybook-dark discovery from Kyle Thompson. A useful next stop after Islets when its strange fairytale world appeals to you.',9),
'Moadra':('One of the newest alien-world discoveries in the collection. Watch the official footage and check the still-growing review sample before treating launch enthusiasm as long-term consensus.',9),
"A Sister's Journey":('A very recent movement-oriented discovery. Best investigated through its current gameplay footage rather than assuming a tiny launch review sample proves lasting polish.',9),
'Echo Weaver':('A time-and-knowledge exploration twist for players who want a fresh world-unlocking idea rather than another familiar weapon ladder.',9),
'Lone Fungus':('A particularly good movement-and-platforming choice, with lots of room to test what newly acquired abilities can do.',9),
'Lone Fungus: Melody of Spores':('For more of the mushroom-world exploration branch. Compare its footage with the first game rather than treating a related title as the same campaign.',9),
'Rusted Moss':('The grappling hook is the main attraction. A distinctive choice for players who enjoy mastering an unconventional movement system.',9),
'Pseudoregalia':('A short, striking 3D exploration adventure where movement mastery matters. A strong route into the genre\'s third-person side.',9),
'Frogmonster':('First-person shooting and ability-led exploration with an unusual creature-filled world. It also belongs to the shooter collection without becoming a duplicate record.',9),
'Vomitoreum':('A surreal, grotesque first-person world with Metroidvania structure. Keep this on the 3D shelf rather than comparing its presentation with a 2D platformer.',8),
'Depths of Sanity':('A distinctive underwater science-fiction and horror adventure. Worth examining when the standard castle-and-forest settings feel too familiar.',9),
'Haiku, the Robot':('A compact robot-world adventure with readable pixel art and conventional interconnected exploration. A useful smaller-scale alternative to the longest games here.',9),
'Yoku\'s Island Express':('Pinball movement and an interconnected island make this one of the most unusual ways to enjoy the genre. A calmer alternative to boss-heavy combat picks.',9),
'Crypt Custodian':('A top-down exploration choice with its own perspective and movement feel. Not a 2D side-scroller disguised by the genre label.',9),
'Minishoot\' Adventures':('A top-down exploration adventure built around shooting and movement upgrades. A useful bridge between bullet-dodging action and world-unlocking discovery.',9),
'Alruna and the Necro-Industrialists':('A compact, distinctive deep cut for players who enjoy experimenting with routes and abilities rather than only following the obvious critical path.',8),
'Alruna: End of History':('A newer entry in the Alruna branch, kept separate from the earlier campaign. Check the current review count alongside the recommendation.',8),
'Biogun':('A colorful microscopic science-fiction adventure. A strong thematic change from dark castles, with the official footage doing a better job than a generic genre description.',9),
'Guns of Fury':('Run-and-gun spectacle coupled with exploration. A promising fit when you want firearms and explosive action instead of another sword-focused adventure.',9),
'Monster Sanctuary':('Turn-based monster battles inside an ability-gated exploration world. A worthwhile hybrid, explicitly not a real-time action platformer.',9),
'Rain World':('A demanding survival ecosystem and exploration neighbor. Do not choose it expecting the standard permanent combat-upgrade ladder.',8)
}
for name,(why,fit) in reasons.items():setgame(name,curatorWhy=why,fit=fit)
setgame('Sheepo',curatorWhy='A compact, transformation-led adventure where traversal rather than conventional weapon combat is the central appeal.',fit=9)
setgame('Castlevania Advance Collection',aliases=['Castlevania: Circle of the Moon','Circle of the Moon','Castlevania: Harmony of Dissonance','Harmony of Dissonance','Castlevania: Aria of Sorrow','Aria of Sorrow','Castlevania: Dracula X'],genreScope='Metroidvania collection / mixed formats',recommendationCaution='Includes three Metroidvanias and the stage-based Dracula X. One official bundle, not four duplicate purchase records.')
setgame('Castlevania Dominus Collection',aliases=['Castlevania: Dawn of Sorrow','Dawn of Sorrow','Castlevania: Portrait of Ruin','Portrait of Ruin','Castlevania: Order of Ecclesia','Order of Ecclesia','Haunted Castle','Haunted Castle Revisited'],genreScope='Metroidvania collection / mixed formats',recommendationCaution='The three DS adventures are Metroidvanias; Haunted Castle and its revisited version are stage-based extras.')
for n in ['ANIMAL WELL','La-Mulana','La-Mulana 2',"Alwa's Awakening","Alwa's Legacy",'Astalon: Tears of the Earth','Phoenotopia: Awakening','Batbarian: Testament of the Primordials','Exographer','Echo Weaver']:
 setgame(n,genreScope='Puzzle-led Metroidvania')
for n in ['Supraland','Supraland Six Inches Under','Supraworld','Pseudoregalia','Frogmonster','Vomitoreum','Maseylia: Echoes of the Past']:
 setgame(n,genreScope='3D Metroidvania')
for n in ['Crypt Custodian',"Minishoot' Adventures"]:setgame(n,genreScope='Top-down Metroidvania')
setgame('Monster Sanctuary',genreScope='Turn-based RPG / Metroidvania hybrid')
setgame('Rain World',genreScope='Survival exploration / Metroidvania-adjacent')
setgame('Greak: Memories of Azur',genreScope='Narrative puzzle adventure / Metroidvania-adjacent')
setgame('The Vagrant',genreScope='Stage-based action RPG / Metroidvania-adjacent')
setgame('Knytt Classic',originalReleaseYear=2006,genreScope='Atmospheric exploration / Metroidvania-adjacent',recommendationCaution='The Steam date describes a later storefront edition of the 2006 freeware classic.')
setgame('Cave Story+',originalReleaseYear=2004,genreScope='Narrative exploration / Metroidvania-adjacent')
setgame('Silent Paradise Anthology',aliases=['Distant Paradise','Silent Paradise'],curatorWhy='A collected creator-world release. Distant Paradise remains searchable as part of its lineage rather than becoming an accidental duplicate purchase recommendation.',storefronts=[{'provider':'itch.io','url':'https://dreamnoid.itch.io/distant-paradise','kind':'archive','verified':True,'lastChecked':'2026-10-23T17:22:47+00:00','sourceUrl':'https://dreamnoid.itch.io/distant-paradise','editionNote':'Original creator-hosted Distant Paradise. The Steam anthology is a separate collected edition.'}])
for g in rows:
 if g['id'].startswith('external:') and g['collection']=='Freeware & creator-hosted worlds' and g['name'] not in ['Hero Core','Lyle in Cube Sector','An Untitled Story','Treasure Adventure Game','Momodora II','A Mini Falafel Adventure']:
  overrides.setdefault(g['id'],{})['confidence']='Exploratory'
 if g['id']=='external:mongrel-story':overrides.setdefault(g['id'],{}).update(name='Mongrel Story (Demo)',recommendationCaution='A creator-hosted pre-alpha demo, not the unrelated commercial game Mongrel. The creator discloses AI-assisted graphics on the source page.')
 if g.get('comingSoon'):overrides.setdefault(g['id'],{})['recommendationCaution']='Unreleased watchlist entry. Interest level is not a scored recommendation or a claim of a completed review.'
(R/'data/metroidvania-curation.json').write_text(json.dumps({'schemaVersion':1,'editorialBasis':'Genre fit and source-supported mechanics, not claimed hands-on reviews. Steam reception and your personal rating remain independent.','overrides':overrides},ensure_ascii=False,indent=2)+'\n')
print('Editorial records:',len(overrides))
