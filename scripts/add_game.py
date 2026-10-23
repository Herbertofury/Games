#!/usr/bin/env python3
"""Import an owner-reviewed issue through structured fields; never execute issue content."""
import csv,json,os,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
event=json.loads(pathlib.Path(os.environ['GITHUB_EVENT_PATH']).read_text());issue=event['issue'];sender=event.get('sender',{}).get('login','');owner=os.environ['GITHUB_REPOSITORY'].split('/')[0]
if sender.lower()!=owner.lower():print('Public suggestion preserved for owner review; no canonical data changed.');sys.exit(0)
body=issue.get('body') or ''
def field(name):
    m=re.search(r'^### '+re.escape(name)+r'\s*\n(.*?)(?=^### |\Z)',body,re.M|re.S);return m.group(1).strip() if m else ''
raw=field('Steam URL or app ID');m=re.fullmatch(r'(?:https://store\.steampowered\.com/app/)?(\d+)(?:/[^\s]*)?',raw)
if not m:raise ValueError('Provide a numeric app ID or an official Steam app URL')
appid=m.group(1);name=field('Game title');collection=field('Collection');fit=field('Editorial fit')
if not name or '\t' in name or '\n' in name:raise ValueError('A single-line title is required')
if not collection or '\t' in collection or '\n' in collection:raise ValueError('A single-line collection is required')
if not re.fullmatch(r'(?:10|[1-9])',fit):raise ValueError('Editorial fit must be 1 through 10')
p=ROOT/'data/seeds.tsv';rows=list(csv.DictReader(p.open(),delimiter='\t'));row={'appid':appid,'name':name,'collection':collection,'fit':fit};old=next((r for r in rows if r['appid']==appid),None)
if old:old.update(row)
else:rows.append(row)
with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=['appid','name','collection','fit'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
print('Updated canonical selection for Steam app',appid)
