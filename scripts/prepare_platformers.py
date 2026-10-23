#!/usr/bin/env python3
"""Reviewed, idempotent discovery corrections. No fuzzy sequel substitutions."""
import csv, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/'scripts/collect_platformers.py'
s=path.read_text()
old="value = unicodedata.normalize('NFKD', value.casefold().replace('&', 'and'))"
new="value = unicodedata.normalize('NFKD', value.replace('\\u2122', '').replace('\\u00ae', '').replace('\\u00a9', '').casefold().replace('&', 'and'))"
if old in s:s=s.replace(old,new)
elif new not in s:raise SystemExit('Collector normalization changed; review before patching')
if '# Reviewed current-title aliases' not in s:
    marker='def accepted(seed, title):'
    assert marker in s
    s=s.replace(marker,"""# Reviewed current-title aliases preserve stable app identities.
ALIASES.update({
    'Big Hops': ['Big Hops Together'],
    'Demon Turf': ['Demon Turf: Queens Edition'],
    'kuso': ['LOVE 2: kuso'],
    'Lone Fungus 2': ['Lone Fungus: Melody of Spores'],
    'Nikoderiko: The Magical World': [\"Nikoderiko: The Magical World - Director's Cut\", 'Nikoderiko: The Magical World \\u2014 Director\\u2019s Cut'],
})
# Avoid a burst of public store requests. Reviews use a separate host.
import time
_get_unthrottled = steam.get
_request_lock = threading.Lock()
_next_request = [0.0]
def polite_get(url):
    if urllib.parse.urlsplit(url).hostname == 'store.steampowered.com':
        with _request_lock:
            delay = max(0.0, _next_request[0] - time.monotonic())
            if delay: time.sleep(delay)
            _next_request[0] = time.monotonic() + 0.75
    return _get_unthrottled(url)
steam.get = polite_get

"""+marker)
path.write_text(s)
p=ROOT/'data/platformers-seeds.tsv'
rows=list(csv.DictReader(p.open(),delimiter='\t'))
ids={'Constance':2313700,'Big Hops':1221480,'Blade Chimera':2671230,'The Smurfs - Dreams':2602020,'Lone Fungus 2':2463220,'Aureole - Wings of Hope':2387460,'MIO: Memories in Orbit':1672810,'Demon Tides':2585890,'GRIME II':2529790,'Duskfade':2542020,'Nikoderiko: The Magical World':2374190}
for row in rows:
    if row['name'] in ids:row['appid']=str(ids[row['name']])
    if row['name']=='Aureole - Wings of Hope':row['collection']='Speed & expressive movement'
    if row['name']=='ibb & obb':row.update(fit='8',appid='95400')
    if row['name']=="New Super Lucky's Tale":row['appid']='1038300'
# Extra routes and omissions found in the first breadth audit. Hints still have
# to pass the same exact official identity check as every other candidate.
more=[
('Cave Story+','Exploration & Metroidvanias',9,'no',200900),
("Shantae: Risky's Revenge - Director's Cut",'Exploration & Metroidvanias',8,'yes',277890),
("Shantae and the Pirate's Curse",'Exploration & Metroidvanias',9,'yes',345820),
('Shantae: Half-Genie Hero','Action & retro adventures',8,'yes',253840),
('Shantae and the Seven Sirens','Exploration & Metroidvanias',8,'yes',1191630),
('Shantae Advance: Risky Revolution','Action & retro adventures',8,'yes',0),
('Levelhead','Precision & mastery',9,'yes',792710),
('Will You Snail?','Precision & mastery',9,'yes',1115050),
('Splasher','Precision & mastery',9,'yes',446840),
('Super Fancy Pants Adventure','Speed & expressive movement',8,'yes',388700),
('Sephonie','3D worlds & collectathons',9,'yes',1248840),
("Lorn's Lure",'3D worlds & collectathons',8,'yes',1417930),
('BETON BRUTAL','Precision & mastery',8,'yes',2330500),
('Crumble','Speed & expressive movement',8,'yes',1061180),
('Marble It Up! Ultra','Speed & expressive movement',8,'yes',864060),
('Papo & Yo','Puzzles & cinematic journeys',8,'yes',227080),
('Anodyne 2: Return to Dust','3D worlds & collectathons',8,'yes',877810),
('Knytt Underground','Exploration & Metroidvanias',8,'yes',248190),
('The Upturned','3D worlds & collectathons',8,'yes',1717770),
('Gecko Gods','3D worlds & collectathons',9,'yes',1290760),
('Teeto','3D worlds & collectathons',8,'yes',0),
('The House of Hikmah','Puzzles & cinematic journeys',8,'yes',0),
('TowerFall Ascension','Co-op & playful chaos',9,'no',251470),
('Vernal Edge','Exploration & Metroidvanias',8,'yes',1546710),
('BioGun','Exploration & Metroidvanias',8,'yes',1219240),
('Fallen Tear: The Ascension','Exploration & Metroidvanias',8,'no',1446900),
('Aestik','Exploration & Metroidvanias',8,'yes',2199330),
('Ato','Exploration & Metroidvanias',9,'yes',1096180),
('Ghost Song','Exploration & Metroidvanias',8,'yes',347800),
("8Doors: Arum's Afterlife Adventure",'Exploration & Metroidvanias',8,'yes',1229150),
('Souldiers','Exploration & Metroidvanias',7,'no',1419160),
('Gato Roboto','Exploration & Metroidvanias',9,'yes',916730),
('KUNAI','Exploration & Metroidvanias',8,'yes',1001800),
('Xanthiom Zero','Exploration & Metroidvanias',8,'yes',0),
('Outland','Action & retro adventures',8,'yes',305050),
('DuckTales: Remastered','Action & retro adventures',8,'no',237630),
('Castle of Illusion','Action & retro adventures',8,'no',227600),
('Disney Epic Mickey 2: The Power of Two','3D worlds & collectathons',7,'no',245300),
('PAC-MAN WORLD Re-PAC','3D worlds & collectathons',8,'no',1859470),
('PAC-MAN WORLD 2 Re-PAC','3D worlds & collectathons',8,'no',0),
('TY the Tasmanian Tiger','3D worlds & collectathons',8,'yes',411960),
('TY the Tasmanian Tiger 2: Bush Rescue','3D worlds & collectathons',8,'yes',411970),
('TY the Tasmanian Tiger 3: Night of the Quinkan','3D worlds & collectathons',7,'yes',411980),
('Sonic Lost World','Speed & expressive movement',7,'no',329440),
('Sonic Origins','Action & retro adventures',8,'no',1794960),
('Unruly Heroes','Co-op & playful chaos',8,'yes',780350),
('Cursed Castilla (Maldita Castilla EX)','Action & retro adventures',8,'yes',534290),
('Chained Together','Co-op & playful chaos',8,'no',2567870),
('PEAK','Co-op & playful chaos',9,'no',3527290),
('Getting Over It with Bennett Foddy','Precision & mastery',8,'no',240720),
('A Difficult Game About Climbing','Precision & mastery',8,'yes',2497920),
('Boomerang X','Speed & expressive movement',9,'yes',1170060),
('Echo Point Nova','Speed & expressive movement',9,'no',1836730),
('Luna Abyss','Puzzles & cinematic journeys',8,'no',1933000),
]
known={r['name'] for r in rows}
for name,collection,fit,gem,appid in more:
    if name not in known:rows.append(dict(name=name,collection=collection,fit=str(fit),gem=gem,appid=str(appid)))
with p.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['name','collection','fit','gem','appid'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
print('Prepared',len(rows),'discovery candidates')
