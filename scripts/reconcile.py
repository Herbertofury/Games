#!/usr/bin/env python3
"""Reconcile a confirmed title change without discarding its discovery history."""
import csv,datetime,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=root/'data/seeds.tsv'
rows=list(csv.DictReader(p.open(),delimiter='\t')); changed=False
for row in rows:
    if row['appid']=='3075410' and row['name']=='Hordes of Fate: A Hand of Fate Adventure':
        old=row['name'];row['name']='Hand of Fate: Hordes';changed=True
        (root/'data/name-history.json').write_text(json.dumps([{'appid':3075410,'previousName':old,'canonicalName':row['name'],'source':'https://store.steampowered.com/app/3075410/','verifiedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}],indent=2)+'\n')
if changed:
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['appid','name','collection','fit'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    subprocess.run([sys.executable,str(root/'scripts/refresh.py')],check=True)
