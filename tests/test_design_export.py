import copy,json,unittest
from datetime import datetime,timezone
from scripts.export_design_catalog import project,select,freshness,review_scope,ROOT
class ExportTests(unittest.TestCase):
 def setUp(self):
  self.cat=json.loads((ROOT/'data/catalog.json').read_text());self.now=datetime(2026,11,17,tzinfo=timezone.utc);self.rows=project(self.cat,now=self.now)
 def test_complete_identity(self):self.assertEqual(len(self.rows),sum(r['id'].startswith('steam:') for r in self.cat['items']))
 def test_rating_label(self):self.assertTrue(all(r['review']['label']=='Overwhelmingly Positive' for r in select(self.rows,label='overwhelmingly positive')))
 def test_combined_filters(self):
  rows=select(self.rows,genre='Action',feature='Single-player',min_count=100,sort='rating');self.assertTrue(rows)
  self.assertTrue(all('Action'in r['genres'] and 'Single-player'in r['features'] and r['review']['count']>=100 for r in rows))
  vals=[r['review']['positivePercent'] for r in rows if r['review']['positivePercent'] is not None];self.assertEqual(vals,sorted(vals,reverse=True))
 def test_unknown_last(self):
  rows=copy.deepcopy(self.rows[:2]);rows[0]['review']['positivePercent']=None;rows[1]['review']['positivePercent']=0
  self.assertEqual(select(rows,sort='rating')[-1]['id'],rows[0]['id'])
 def test_no_invented_strengths(self):self.assertTrue(all(r['designEvidence']is None and r['editorial']['notPlayerConsensus'] for r in self.rows))
 def test_freshness(self):
  for value,want in [(None,'unknown'),('bad','unknown'),('2026-11-17','unknown'),('2026-12-17T00:00:00+00:00','future_observation'),('2026-10-17T00:00:00+00:00','stale')]:self.assertEqual(freshness(value,self.now),want)
 def test_duplicate_and_bad_identity(self):
  self.cat['items'].append(self.cat['items'][0])
  with self.assertRaises(ValueError):project(self.cat)
  self.cat['items'].pop();r=next(r for r in self.cat['items'] if r['id'].startswith('steam:'));r['appid']=1
  with self.assertRaises(ValueError):project(self.cat)
 def test_review_scope_preserved(self):
  r=next(r for r in self.cat['items'] if r['id']=='steam:1794680');s=review_scope(r);self.assertEqual(s[0]['request']['languages'],['all']);r['appid']=1;self.assertEqual(review_scope(r),[])
 def test_exact_study_join(self):
  r=self.rows[0];study={'id':r['id'],'source_url':r['sourceUrl'],'checked_on':'2026-11-17','evidence_scope':'synthetic test','observations':['synthetic'],'design_interpretation':'hypothesis','acceptance':['test'],'playtest':'not_performed'}
  rows=project(self.cat,{'schema_version':1,'records':[study]},self.now);self.assertEqual(sum(r['designEvidence']is not None for r in rows),1)
