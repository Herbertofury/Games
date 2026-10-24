import json,pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble,game_key
HUB='Couch co-op & party'
class PartyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=json.loads((R/'data/catalog.json').read_text());cls.all={g['id']:g for g in cls.c['items']};cls.by={i:g for i,g in cls.all.items() if HUB in g.get('hubs',[])};cls.rows=list(cls.by.values())
 def test_all_promoted_candidates_unique_and_full_breadth(self):
  raw={g['id'] for f in ['party-steam.json','party-extra.json','party-recovered.json','party-external.json'] for g in json.loads((R/'data'/f).read_text())['items']};cur=json.loads((R/'data/party-curation.json').read_text())['overrides'];held={i for i in raw if cur.get(i,{}).get('excludeFromPublication')};self.assertEqual(set(self.by),raw-held);self.assertEqual(len(raw),347);self.assertGreaterEqual(len(self.rows),330);self.assertEqual(len(self.c['items']),len(self.all))
 def test_all_previous_records_and_memberships_preserved(self):
  p=json.loads((R/'data/party-protected.json').read_text());self.assertEqual(len(p['ids']),1567);self.assertTrue(set(p['ids'])<=set(self.all))
  for ident,hubs in p['hubs'].items():self.assertTrue(set(hubs)<=set(self.all[ident]['hubs']))
 def test_every_game_has_sourced_art_and_supported_video(self):
  for g in self.rows:
   with self.subTest(game=g['name']):
    self.assertEqual(g['verification'],'verified');self.assertTrue(g['image'].startswith('https://'));self.assertTrue(g['trailers']);self.assertTrue(g['storefronts'])
    for t in g['trailers']:
     self.assertTrue(t['sourceUrl'].startswith('https://'));self.assertTrue(any(t.get(k) for k in ['hls','mp4','webm','youtube','vimeo']))
 def test_modes_have_evidence_and_unknown_is_not_zero(self):
  for g in self.rows:
   p=g['partyInfo'];self.assertTrue(p.get('localSupport'));self.assertTrue(p['modesDetail']);self.assertTrue(p['platform']);self.assertTrue(p['inputs'])
   numbers=sorted({n for m in p['modesDetail'] for n in m['counts']});self.assertEqual(numbers,p['playerCounts']);self.assertEqual(bool(numbers),p['countVerified']);self.assertEqual(p['localMax'],max(numbers) if numbers else None)
   for m in p['modesDetail']:
    self.assertIn(m['type'],['Co-op','Versus']);self.assertTrue(m['sourceUrl'].startswith('https://'));self.assertTrue(m['evidenceBasis']);self.assertTrue(all(isinstance(n,int) and n>=2 for n in m['counts']))
 def test_user_favorites_are_present_and_not_just_coop(self):
  for ident in ['steam:415880','steam:261180','steam:553310','steam:833500','steam:556050','steam:965680']:
   self.assertIn(ident,self.by);self.assertTrue(self.by[ident]['knownFavorite']);self.assertIn('Versus',self.by[ident]['partyInfo']['modes'])
  self.assertEqual(self.by['steam:415880']['partyInfo']['playerCounts'],[2,4]);self.assertEqual(self.by['steam:965680']['partyInfo']['playerCounts'],[2,3,4,5,6])
 def test_mode_limits_do_not_become_union_capacities(self):
  self.assertEqual(self.by['steam:4489580']['partyInfo']['coopCounts'],[2]);self.assertEqual(self.by['steam:4489580']['partyInfo']['versusCounts'],list(range(2,9)))
  self.assertEqual(self.by['steam:585710']['partyInfo']['coopCounts'],[2]);self.assertEqual(self.by['steam:477160']['partyInfo']['localMax'],2)
 def test_dlc_and_shared_controller_conditions_are_visible(self):
  modes=self.by['steam:251470']['partyInfo']['modesDetail'];self.assertTrue(any(m['type']=='Co-op' and 4 in m['counts'] and m['requiresDlc'] for m in modes));self.assertFalse(any(m['type']=='Co-op' and 4 in m['counts'] and not m['requiresDlc'] for m in modes))
  p=self.by['steam:538550']['partyInfo'];self.assertTrue(any(8 in m['counts'] and m['notes'] for m in p['modesDetail']))
 def test_spectators_are_not_players_but_lie_swatter_is(self):
  p=self.by['steam:331670']['partyInfo'];self.assertEqual(p['participation'],'phones');self.assertEqual(p['localMax'],100);self.assertTrue(any('Lie Swatter' in m['name'] and 100 in m['counts'] for m in p['modesDetail']))
  self.assertLessEqual(max(g['partyInfo']['localMax'] or 0 for g in self.rows),100)
 def test_cooperative_minigames_keep_their_own_limits(self):
  self.assertEqual(self.by['steam:2216830']['partyInfo']['coopCounts'],list(range(2,10)))
  self.assertTrue(any('Dodo' in m['name'] for m in self.by['steam:2216830']['partyInfo']['modesDetail']))
 def test_edition_phone_hotseat_and_vr_separation(self):
  types={g['partyInfo']['participation'] for g in self.rows};self.assertEqual(types,{'simultaneous','hotseat','phones','asymmetric'});self.assertTrue(any('Nintendo' in g['partyInfo']['platform'] or 'Switch' in g['partyInfo']['platform'] for g in self.rows))
 def test_all_339_are_in_the_complete_atlas(self):
  atlas=(R/'wiki/Party-Media.md').read_text()
  for g in self.rows:
   self.assertIn(game_key(g),atlas);self.assertIn(g['image'],atlas)
   for s in g['storefronts']:self.assertIn(s['url'],atlas)
 def test_new_sidebar_and_storage_are_integrated(self):
  p=(R/'dist/index.html').read_text();self.assertIn('installPartyHub',p);self.assertIn('party-players',p);self.assertIn('games.library.v1',p);self.assertIn('filtered.map(card)',p)
 def test_repeat_build_is_exact_and_not_cumulative(self):
  again=assemble(self.c);self.assertEqual(self.c['items'],again['items']);self.assertEqual(self.c['build']['datasetHash'],again['build']['datasetHash'])
 def test_sources_not_placeholder_searches_or_tracking(self):
  for g in self.rows:
   self.assertEqual(len(g['storefronts']),len({l['url'] for l in g['storefronts']}))
   for l in g['storefronts']:self.assertTrue(l['verified']);self.assertTrue(l['url'].startswith('https://'));self.assertNotIn('utm_',l['url'])
if __name__=='__main__':unittest.main()
