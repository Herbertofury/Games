import json,pathlib,re,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble,game_key,score
@unittest.skipUnless((R/'data/metroidvania-protected.json').exists(), 'Metroidvania source research is present, but its hub installer has not run yet.')
class MetroidvaniaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((R/'data/catalog.json').read_text());cls.rows=[g for g in cls.catalog['items'] if 'Metroidvanias' in g.get('hubs',[])];cls.by={g['id']:g for g in cls.rows}
 def test_enormous_unique_collection(self):
  self.assertGreaterEqual(len(self.rows),300);self.assertEqual(len(self.rows),len(self.by));self.assertEqual(self.catalog['build']['hubCounts']['Metroidvanias'],len(self.rows))
 def test_every_previous_identity_survives(self):
  old=json.loads((R/'data/metroidvania-protected.json').read_text());self.assertEqual(len(old['ids']),448);self.assertTrue(set(old['ids']) <= {g['id'] for g in self.catalog['items']})
  for h,n in [('Roguelites',170),('Boomer shooters',150),('Real-time strategy',130)]:self.assertEqual(sum(h in g['hubs'] for g in self.catalog['items']),n)
 def test_all_entries_have_exact_art_and_video(self):
  for g in self.rows:
   with self.subTest(game=g['name']):
    self.assertTrue(g.get('image','').startswith('https://'));self.assertTrue(g.get('trailers'));self.assertEqual(g['verification'],'verified')
    for t in g['trailers']:
     self.assertTrue(t.get('sourceUrl','').startswith('https://'));self.assertTrue(any(t.get(k) for k in ['hls','mp4','webm','youtube']))
     if t.get('youtube'):self.assertRegex(t['youtube'],r'^[A-Za-z0-9_-]{11}$')
 def test_all_store_buttons_are_confirmed(self):
  for g in self.rows:
   self.assertTrue(g.get('storefronts'));self.assertTrue(any(x['kind']!='support' for x in g['storefronts']))
   self.assertEqual(len(g['storefronts']),len({x['url'] for x in g['storefronts']}))
   for x in g['storefronts']:self.assertTrue(x['verified']);self.assertTrue(x['url'].startswith('https://'));self.assertNotIn('utm_',x['url'])
 def test_future_games_are_not_released_recommendations(self):
  upcoming=[g for g in self.rows if g.get('comingSoon')];self.assertTrue(upcoming)
  for g in upcoming:self.assertEqual(g['status'],'Upcoming');self.assertIsNone(score(g))
 def test_prototypes_and_support_are_distinct(self):
  self.assertTrue(any(g['status'] in ['Prototype','Demo'] for g in self.rows));self.assertTrue(any(l['kind']=='support' for g in self.rows for l in g['storefronts']))
  for g in self.rows:
   if g['status'] in ['Prototype','Demo']:self.assertNotEqual(g['status'],'Released')
 def test_traditional_and_adjacent_formats_are_separate(self):
  self.assertTrue(any('MV core' in g['tags'] for g in self.rows));self.assertTrue(any('MV adjacent / hybrid' in g['tags'] for g in self.rows))
  for g in self.rows:
   self.assertTrue(g.get('metroidvaniaInfo'));self.assertTrue(g['metroidvaniaInfo']['sourceUrl'].startswith('https://'))
   if 'adjacent' in g['metroidvaniaInfo']['structure'].lower():self.assertNotIn('MV core',g['tags'])
 def test_no_duplicate_demo_game_count(self):
  self.assertTrue(any(any(l['kind']=='demo' for l in g['storefronts']) for g in self.rows))
  ids={g.get('appid') for g in self.rows if g.get('appid')}
  for g in self.rows:
   for aid in g.get('demoAppids',[]):self.assertNotIn(aid,ids)
 def test_complete_wiki_atlas(self):
  text=(R/'wiki/Metroidvania-Media.md').read_text()
  for g in self.rows:
   self.assertIn(game_key(g),text);self.assertIn(g['image'],text)
   for link in g['storefronts']:self.assertIn(link['url'],text)
 def test_original_castlevania_titles_are_searchable(self):
  allnames=' '.join(g['name']+' '+' '.join(g.get('aliases',[])) for g in self.rows)
  for title in ['Aria of Sorrow','Dawn of Sorrow','Order of Ecclesia','Symphony of the Night']:self.assertIn(title,allnames)
 def test_repeated_build_preserves_every_record(self):
  a=assemble(self.catalog);self.assertEqual(a['items'],assemble(a)['items'])
 def test_browser_storage_and_all_records_are_retained(self):
  js=(R/'site/app.js').read_text();self.assertIn("const KEY='games.library.v1'",js);self.assertIn('filtered.map(card)',js);self.assertIn('metroidvaniaBrief',js)
if __name__=='__main__':unittest.main()
