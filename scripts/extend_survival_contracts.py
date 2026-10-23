"""Extend the existing exact-union assertion for the newly installed canonical hubs."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'tests/test_platformers.py';s=p.read_text()
old="  self.assertEqual(expected,set(self.by));self.assertEqual(len(self.by),len(self.data['items']))"
new="""  # The catalog has additional canonical hubs; preserve exact equality, not a subset check.
  survival_overrides={}
  for filename in ['survival-curation.json','survival-media.json']:
   path=R/'data'/filename
   if path.exists():
    for ident,row in json.loads(path.read_text()).get('overrides',{}).items():survival_overrides.setdefault(ident,{}).update(row)
  for filename in ['survival-steam.json','survival-external.json']:
   path=R/'data'/filename
   if path.exists():expected.update(g['id'] for g in json.loads(path.read_text())['items'] if not survival_overrides.get(g['id'],{}).get('excludeFromPublication'))
  self.assertEqual(expected,set(self.by));self.assertEqual(len(self.by),len(self.data['items']))"""
if new not in s:
 assert old in s,'Exact source-union assertion changed; review before patching'
 p.write_text(s.replace(old,new,1))
print('Exact source-union regression now covers all installed hubs and explicit exclusions.')
