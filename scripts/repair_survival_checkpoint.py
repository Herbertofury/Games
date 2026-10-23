"""Repair the two precise integration-contract findings from the source gate."""
from pathlib import Path
import runpy
R=Path(__file__).resolve().parents[1]
runpy.run_path(str(R/'scripts/extend_survival_contracts.py'),run_name='__main__')
p=R/'scripts/survival_model.py';s=p.read_text()
old=" return {'ids':sorted(set(ids)),'generatedAt':max(dates) if dates else None,'unresolved':review.get('unresolved',steam.get('unresolved',[])),'dispositions':review.get('dispositions',steam.get('dispositions',[])+external.get('dispositions',[]))+excluded}"
new=""" names={g['id']:g['name'] for g in steam['items']+external['items']}
 dispositions=copy.deepcopy(review.get('dispositions',steam.get('dispositions',[])+external.get('dispositions',[]))+excluded)
 for record in dispositions:
  record.setdefault('candidate',names.get(record.get('id'),record.get('id') or 'Unresolved discovery'))
 return {'ids':sorted(set(ids)),'generatedAt':max(dates) if dates else None,'unresolved':review.get('unresolved',steam.get('unresolved',[])),'dispositions':dispositions}"""
if new not in s:
 assert old in s,'Survival ledger assembly changed; reconcile before patching'
 p.write_text(s.replace(old,new,1))
# Keep the shared-ledger identity contract covered independently of any one older hub.
p=R/'tests/test_survival.py';s=p.read_text()
anchor=" def test_review_counts_and_scores_are_not_conflated(self):"
newtest=""" def test_candidate_ledger_retains_names_and_states(self):
  for row in self.catalog['build']['candidateDispositions']:
   self.assertTrue(row.get('candidate'));self.assertTrue(row.get('state'))
 def test_review_counts_and_scores_are_not_conflated(self):"""
if newtest not in s:
 assert anchor in s
 p.write_text(s.replace(anchor,newtest,1))
print('Both source-gate findings repaired; all recommendation data and original checks remain intact.')
