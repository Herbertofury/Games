"""Every RTS entry and every preserved genre are included in acceptance."""
import json,pathlib,re,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble,score,game_key
class RTSTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((R/'data/catalog.json').read_text());cls.rows=[g for g in cls.data['items'] if 'Real-time strategy' in g.get('hubs',[])];cls.by={g['id']:g for g in cls.rows}
 def test_counts_and_identity(self):
  self.assertEqual(len(self.rows),130);self.assertEqual(len(self.data['items']),self.data['build']['inputCount']);self.assertEqual(len({g['id'] for g in self.data['items']}),len(self.data['items']))
 def test_original_collections_preserved(self):
  self.assertGreaterEqual(sum('Roguelites' in g['hubs'] for g in self.data['items']),171);self.assertEqual(sum('Boomer shooters' in g['hubs'] for g in self.data['items']),150)
 def test_all_images_and_videos(self):
  for g in self.rows:
   with self.subTest(game=g['name']):
    self.assertTrue(g['image'].startswith('https://'));self.assertTrue(g['trailers'])
    for t in g['trailers']:
     self.assertTrue(t.get('sourceUrl','').startswith('https://'));self.assertTrue(any(t.get(k) for k in ['youtube','mp4','webm','hls']))
     if t.get('youtube'):self.assertRegex(t['youtube'],r'^[A-Za-z0-9_-]{11}$')
 def test_all_sources_are_exact(self):
  for g in self.rows:
   self.assertTrue(g['storefronts']);self.assertTrue(any(l['kind']!='support' for l in g['storefronts']))
   urls=[l['url'] for l in g['storefronts']];self.assertEqual(len(urls),len(set(urls)))
   for l in g['storefronts']:
    self.assertTrue(l['verified']);self.assertTrue(l['url'].startswith('https://'));self.assertNotIn('/feed/',l['url']);self.assertNotIn('utm_',l['url'])
 def test_full_rts_atlas(self):
  atlas=(R/'wiki/RTS-Media.md').read_text()
  for g in self.rows:
   self.assertIn(game_key(g),atlas);self.assertIn(g['image'],atlas)
   for link in g['storefronts']:self.assertIn(link['url'],atlas)
 def test_watchlist_is_not_a_purchase_recommendation(self):
  upcoming=[g for g in self.rows if g.get('comingSoon')];self.assertEqual(len(upcoming),6)
  for g in upcoming:self.assertIsNone(score(g));self.assertEqual(g['status'],'Upcoming')
 def test_mod_requirements_distinguish_base_games(self):
  for i in ['contra-x','rise-of-the-reds','cc-shockwave','end-of-days-zh']:self.assertIn('Zero Hour',self.by['external:'+i]['requirements'])
  self.assertIn('Red Alert 3',self.by['external:generals-evolution']['requirements']);self.assertIn("Yuri's Revenge",self.by['external:mental-omega']['requirements'])
 def test_tactical_games_are_not_classified_as_base_builders(self):
  for ident in ['steam:1611600','steam:1604270','steam:251060','external:world-in-conflict']:
   self.assertIn('No conventional',self.by[ident]['rtsInfo']['baseBuilding']);self.assertNotIn('Zero Hour-like',self.by[ident]['tags'])
 def test_demo_and_older_builds_are_not_full_games(self):
  expected={'steam:1272320':'demo','steam:3213120':'prototype','steam:1113030':'prototype','steam:2088550':'project'}
  for ident,kind in expected.items():self.assertEqual(next(l['kind'] for l in self.by[ident]['storefronts'] if l['provider']=='itch.io'),kind)
 def test_no_generic_ui_assets_as_artwork(self):
  for g in self.rows:self.assertNotRegex(g['image'],r'dlbtn_|unmuted|butt_play|_avm\d?\.')
  for ident in ['external:warcraft-1-remastered','external:warcraft-2-remastered']:
   self.assertEqual(self.by[ident]['trailers'][0]['youtube'],'ryZ2jiW95qo');self.assertIn('Battle Chest',self.by[ident]['trailers'][0]['editionNote'])
 def test_old_release_dates_stay_distinct(self):
  self.assertEqual(self.by['steam:2732960']['originalReleaseYear'],2003);self.assertEqual(self.by['steam:254760']['originalReleaseYear'],2001)
 def test_unknown_and_cancelled_candidates_are_retained_in_ledger(self):
  ledger=self.data['build']['candidateDispositions'];names={x['candidate']:x['state'] for x in ledger}
  self.assertEqual(names['Battle Aces'],'excluded');self.assertEqual(names['Rise of Legends'],'unresolved-active')
 def test_repeated_build_does_not_duplicate_or_change_records(self):
  a=assemble(self.data);self.assertEqual(a['items'],assemble(a)['items'])
 def test_clear_caution_on_low_evidence(self):
  g=self.by['steam:5265230'];self.assertLessEqual(score(g),5);self.assertTrue(g['recommendationCaution'])
 def test_saved_state_namespace_is_unchanged(self):
  self.assertIn("const KEY='games.library.v1'",(R/'site/app.js').read_text())
if __name__=='__main__':unittest.main()
