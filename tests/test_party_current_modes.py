import json,pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class PartyCurrentModeTests(unittest.TestCase):
 def test_current_samurai_gunn_relaunch_is_not_cooperative(self):
  c=json.loads((R/'data/catalog.json').read_text());g=next(g for g in c['items'] if g['id']=='steam:1397790');p=g['partyInfo']
  self.assertEqual(p['modes'],['Versus']);self.assertEqual(p['coopCounts'],[]);self.assertEqual(p['playerCounts'],[2])
  self.assertEqual(len(p['modesDetail']),2);self.assertTrue(any(m['name']=='Local free-for-all' and not m['counts'] for m in p['modesDetail']))
  self.assertIn('removed Adventure',p['notes']);self.assertEqual(g['originalReleaseYear'],2021);self.assertNotIn('Recent couch release',g['tags'])
  evidence=json.loads((R/'data/party-current-mode-review.json').read_text());self.assertTrue(evidence['removedAdventure']);self.assertTrue(evidence['local1v1Implemented'])
if __name__=='__main__':unittest.main()
