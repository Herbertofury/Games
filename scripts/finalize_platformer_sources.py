#!/usr/bin/env python3
"""Finish reviewed identity reconciliation; preserve a before/after evidence file."""
import csv,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
qa=ROOT/'qa';qa.mkdir(exist_ok=True)
source=ROOT/'data/catalog.json';catalog=json.loads(source.read_text())
baseline=qa/'platformers-baseline.json'
if not baseline.exists():baseline.write_text(json.dumps({'items':catalog['items'],'build':catalog.get('build',{})},ensure_ascii=False,indent=2)+'\n')
p=ROOT/'scripts/collect_platformers.py';s=p.read_text()
anchor="ALIASES = {\n"
addition="ALIASES = {\n    'TY the Tasmanian Tiger 2: Bush Rescue': ['TY the Tasmanian Tiger 2'],\n    'TY the Tasmanian Tiger 3: Night of the Quinkan': ['TY the Tasmanian Tiger 3'],\n"
if addition not in s:
 assert s.count(anchor)==1
 p.write_text(s.replace(anchor,addition,1))
# These exact official product pages explicitly identify their longer subtitles
# in the description. The aliases do not accept another sequel or a soundtrack.
subprocess.run([sys.executable,str(ROOT/'scripts/collect_platformers.py'),'--workers','2'],check=True)
import collect_platformers as collector
seeds=list(csv.DictReader((ROOT/'data/seeds.tsv').open(),delimiter='\t'))
ids={str(g.get('appid')) for g in catalog['items'] if g.get('appid')}
added=[]
for seed in seeds:
 if seed['appid'] in ids:continue
 # Never silently alter a seed identity during the pending-source repair.
 details=collector.cached_details(int(seed['appid']))
 assert details and details.get('type')=='game' and collector.norm(seed['name'])==collector.norm(details['name']),seed
 game=collector.steam.resolve(seed,{},True)
 assert game.get('verification')=='verified' and str(game.get('appid'))==seed['appid'],game
 catalog['items'].append(game);ids.add(seed['appid']);added.append(game['id'])
if added:
 catalog['generatedAt']=collector.NOW
 source.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
(qa/'platformers-source-finalization.json').write_text(json.dumps({'addedOriginalSeeds':added,'reviewedAliases':[{'appid':411970,'source':'https://store.steampowered.com/app/411970/','note':'Official description identifies the Bush Rescue remaster.'},{'appid':411980,'source':'https://store.steampowered.com/app/411980/','note':'Official description identifies the Night of the Quinkan remaster.'}],'originalSeedCount':len(seeds)},indent=2)+'\n')
print('Pending original seeds imported:',added)
