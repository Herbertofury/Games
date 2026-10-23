"""Install targeted continuity/freshness guards in the reusable collector."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'scripts/enrich_metroidvania.py';s=p.read_text()
marker=' # Preserve canonical IDs and all previously resolved candidates across index changes.\n'
if marker not in s:
 old=' accepted=[]\n'
 new=""" # Preserve canonical IDs and all previously resolved candidates across index changes.
 explicit={core.key(x['name']):x for x in load('metroidvania-completion-plan.json',{}).get('steam',[])}
 previous={core.key(g.get('seedName',g['name'])):g for g in old}
 present={core.key(x['name']) for x in candidates}
 for g in old:
  k=core.key(g.get('seedName',g['name']))
  if k not in present:
   candidates.append({'name':g.get('seedName',g['name']),'appid':g['appid'],'aliases':list(dict.fromkeys(g.get('aliases',[])+[g['name']])),'collection':g['collection'],'fit':g.get('fit') or 8,'scope':g.get('genreScope','Traditional Metroidvania'),'discoverySource':'Retained canonical identity'})
   present.add(k)
 for x in candidates:
  k=core.key(x['name'])
  if k in explicit:x.update(explicit[k])
  elif not x.get('appid') and k in previous:
   g=previous[k];x['appid']=g['appid'];x['aliases']=list(dict.fromkeys(x.get('aliases',[])+[g['name']]))
 accepted=[]
"""
 assert old in s;s=s.replace(old,new,1)
if 'def external_phase(seed,old,force=False):' not in s:
 s=s.replace('def external_phase(seed,old):','def external_phase(seed,old,force=False):',1)
 old=" if prior and prior.get('image') and prior.get('trailers'):return prior"
 new=" if prior and not force and prior.get('image') and prior.get('trailers') and prior.get('mediaCheckedAt'):\n  if (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(prior['mediaCheckedAt'])).total_seconds()<86400:return prior"
 assert old in s;s=s.replace(old,new,1).replace('external_phase(s,old),','external_phase(s,old,a.force),',1)
if 'def store_phase(g,old,itch_ready,force=False):' not in s:
 s=s.replace('def store_phase(g,old,itch_ready):','def store_phase(g,old,itch_ready,force=False):',1)
 old=" if old and old.get('storeCoverage',{}).get('checkedAt'):return g['id'],old"
 new=" if old and not force and old.get('storeCoverage',{}).get('checkedAt'):\n  if (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(old['storeCoverage']['checkedAt'])).total_seconds()<604800:return g['id'],old"
 assert old in s;s=s.replace(old,new,1).replace("store_phase(g,overrides.get(g['id']),itch_ready)","store_phase(g,overrides.get(g['id']),itch_ready,a.force)",1)
p.write_text(s)
print('Stable IDs, retained discoveries, and explicit creator/store cache invalidation protected.')
