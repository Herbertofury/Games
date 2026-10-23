"""Coverage and edition invariants for every published shooter, not a sample."""
import json,pathlib,re,sys,unittest,urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from catalog_model import game_key,assemble
from source_links import canonical_listing,normalized_links
class SourceCompletionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.games=[g for g in cls.catalog['items'] if 'Boomer shooters' in g.get('hubs',[])];cls.by={g['id']:g for g in cls.games}
 def test_every_shooter_has_visual_and_video(self):
  self.assertGreaterEqual(len(self.games),150)
  for g in self.games:
   with self.subTest(game=g['name']):
    self.assertTrue(g.get('image','').startswith('https://'))
    self.assertTrue(any(t.get('youtube') or t.get('mp4') or t.get('webm') or t.get('hls') for t in g.get('trailers',[])))
    for t in g['trailers']:
     self.assertTrue(t.get('sourceUrl','').startswith('https://'))
     if t.get('youtube'):self.assertRegex(t['youtube'],r'^[A-Za-z0-9_-]{11}$')
 def test_every_shooter_has_real_distribution(self):
  for g in self.games:
   with self.subTest(game=g['name']):
    self.assertTrue(any(s['kind']!='support' for s in g['storefronts']))
    for s in g['storefronts']:
     self.assertTrue(s.get('verified'));self.assertTrue(s['url'].startswith('https://'))
     self.assertNotIn('utm_',s['url']);self.assertNotIn('itch.io/games-like/',s['url']);self.assertNotIn('/devlog/',s['url'])
 def test_every_shooter_in_media_atlas(self):
  s=(ROOT/'wiki/Boomer-Shooters-Media.md').read_text()
  for g in self.games:
   with self.subTest(game=g['name']):
    self.assertIn(g['image'],s);self.assertIn(game_key(g),s)
    for x in g['storefronts']:self.assertIn(x['url'],s)
 def test_demo_links_not_full_game_stores(self):
  for ident in ['steam:1840610','steam:1396870','steam:1409200','steam:1640300','steam:1677900','steam:1779060']:
   self.assertEqual(next(s for s in self.by[ident]['storefronts'] if s['provider']=='itch.io')['kind'],'demo')
  self.assertEqual(next(s for s in self.by['steam:1665260']['storefronts'] if s['provider']=='itch.io')['kind'],'project')
 def test_mod_and_remake_media_are_not_confused(self):
  g=self.by['external:total-chaos-original'];self.assertFalse(any(t.get('youtube')=='guO_QkSFOTE' for t in g['trailers']))
  self.assertTrue(any('total_chaos_mod' in s['url'] for s in g['storefronts']))
  self.assertTrue(self.by['external:death-wish']['trailers'][0].get('editionNote'))
  self.assertFalse(self.by['external:arcane-dimensions']['trailers'][0]['official'])
 def test_provider_normalization_keeps_curated_downloads(self):
  self.assertEqual(canonical_listing('https://www.moddb.com/mods/g-string/reviews'),'https://www.moddb.com/mods/g-string')
  self.assertIsNone(canonical_listing('https://itch.io/games-like/123/foo'))
  self.assertEqual(canonical_listing('https://dev.itch.io/game/devlog/1/news'),'https://dev.itch.io/game')
  self.assertEqual(len(normalized_links([{'url':'https://www.moddb.com/mods/x/reviews'},{'url':'https://www.moddb.com/mods/x/forum'}])),1)
  a=assemble(self.catalog);self.assertEqual(a['items'],assemble(a)['items'])
 def test_research_coverage_reconciles(self):
  d=json.loads((ROOT/'data/storefront-discovery.json').read_text());r=json.loads((ROOT/'data/storefront-discovery-report.json').read_text())
  self.assertEqual(r['gamesChecked'],126);self.assertEqual(len(d['coverage']),126)
  self.assertEqual(r['confirmedLinks'],sum(len(x.get('storefronts',[])) for x in d['overrides'].values()))
if __name__=='__main__':unittest.main()
