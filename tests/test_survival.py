import json,pathlib,re,sys,unittest,urllib.parse
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble,game_key,score
HUBS=('Survival','Minecraft-like worlds')
class SurvivalContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((R/'data/catalog.json').read_text());cls.rows=[g for g in cls.catalog['items'] if any(h in g['hubs'] for h in HUBS)];cls.by={g['id']:g for g in cls.rows};cls.old=json.loads((R/'data/survival-protected.json').read_text())
 def test_enormous_separate_hubs(self):
  self.assertGreaterEqual(len(self.rows),350)
  self.assertGreaterEqual(sum(HUBS[1] in g['hubs'] for g in self.rows),70)
  for h in HUBS:self.assertEqual(sum(h in g['hubs'] for g in self.rows),self.catalog['build']['hubCounts'][h])
 def test_no_previous_identity_or_membership_lost(self):
  self.assertEqual(len(self.old['ids']),1189);self.assertTrue(set(self.old['ids'])<={g['id'] for g in self.catalog['items']})
  for h,n in self.old['hubCounts'].items():self.assertEqual(self.catalog['build']['hubCounts'][h],n)
 def test_named_user_references_are_present_in_the_correct_hub(self):
  for ident in ['steam:440900','steam:2399830','steam:346110','steam:3041230']:self.assertIn(HUBS[0],self.by[ident]['hubs'])
  for ident in ['external:minecraft','external:vintage-story','external:hytale','steam:105600']:self.assertIn(HUBS[1],self.by[ident]['hubs']);self.assertNotIn(HUBS[0],self.by[ident]['hubs'])
 def test_every_published_game_has_art_and_supported_video(self):
  for g in self.rows:
   with self.subTest(game=g['name']):
    self.assertEqual(g['verification'],'verified');self.assertTrue(g.get('image','').startswith('https://'));self.assertTrue(g.get('trailers'))
    for t in g['trailers']:
     self.assertTrue(t.get('sourceUrl','').startswith('https://'));self.assertTrue(any(t.get(k) for k in ['hls','mp4','webm','youtube','vimeo']))
     if t.get('youtube'):self.assertRegex(t['youtube'],r'^[A-Za-z0-9_-]{11}$')
 def test_all_destinations_are_exact_and_confirmed(self):
  for g in self.rows:
   links=g['storefronts'];self.assertTrue(links);self.assertEqual(len(links),len({x['url'].rstrip('/') for x in links}))
   self.assertTrue(any(x['kind'] not in ['support','archive'] for x in links))
   for x in links:
    self.assertTrue(x['verified']);self.assertTrue(x['url'].startswith('https://'));self.assertNotIn('utm_',x['url']);self.assertNotIn('/search?',x['url']);self.assertNotIn(x['kind'],['news','media','engine'])
    if x['provider']=='GitHub':self.assertNotEqual(x['kind'],'store')
 def test_edition_and_server_boundaries_are_visible(self):
  self.assertFalse(self.by['external:minecraft']['free']);self.assertFalse(self.by['external:hytale']['free']);self.assertFalse(self.by['external:vintage-story']['free'])
  self.assertEqual(self.by['external:hytale']['status'],'Early Access');self.assertEqual(self.by['steam:3041230']['status'],'Early Access')
  for g in self.rows:self.assertTrue(g.get('survivalInfo'));self.assertTrue(g['survivalInfo']['sourceUrl'].startswith('https://'));self.assertTrue(g['survivalInfo']['basis'])
 def test_creator_archive_does_not_masquerade_as_purchase(self):
  vintage=self.by['external:vintage-story'];itch=[s for s in vintage['storefronts'] if 'tyronx.itch.io' in s['url']];self.assertTrue(itch);self.assertTrue(all(s['kind']=='archive' for s in itch))
  raft=[s for s in self.by['steam:648800']['storefronts'] if 'raft.itch.io' in s['url']];self.assertTrue(all(s['kind'] in ['prototype','archive'] for s in raft))
 def test_mod_engines_and_translations_are_not_game_stores(self):
  for g in self.rows:
   for x in g['storefronts']:self.assertNotIn('Lucid-Blocks-Chinese-Localization',x['url']);self.assertNotIn('stardeus-mod-template',x['url'])
  for ident in ['external:voxelibre','external:mineclonia']:self.assertIn('Luanti',self.by[ident]['requirements'])
 def test_upcoming_not_scored_as_released(self):
  future=[g for g in self.rows if g.get('comingSoon')];self.assertTrue(future)
  for g in future:self.assertEqual(g['status'],'Upcoming');self.assertIsNone(score(dict(g,fit=g.get('survivalFit'))))
 def test_original_dates_do_not_become_new_releases(self):
  for ident,year in [('steam:105600',2011),('steam:892970',2021),('steam:1203620',2024)]:
   g=self.by[ident];self.assertEqual(g.get('originalReleaseYear'),year);self.assertNotIn('Recent survival release',g['tags'])
 def test_related_formats_are_not_in_the_core_filter(self):
  for g in self.rows:
   if any(t in g.get('survivalScope','').lower() for t in ['adjacent','colony','experimental','turn-based']):self.assertNotIn('Survival core',g['tags'])
  self.assertEqual(self.by['steam:105600']['survivalCollection'],'Terraria-like 2D worlds')
 def test_every_record_occurs_in_its_wiki_atlas(self):
  for h,name in [('Survival','Survival-Media'),('Minecraft-like worlds','Minecraft-Like-Media')]:
   s=(R/'wiki'/(name+'.md')).read_text()
   for g in self.rows:
    if h not in g['hubs']:continue
    self.assertIn(game_key(g),s);self.assertIn(g['image'],s)
    for l in g['storefronts']:self.assertIn(l['url'],s)
 def test_repeat_build_is_idempotent(self):
  a=assemble(self.catalog);self.assertEqual(a['items'],assemble(a)['items'])
 def test_zero_loss_personal_storage_and_rendering(self):
  js=(R/'site/app.js').read_text();new=(R/'site/survival.js').read_text();self.assertIn("const KEY='games.library.v1'",js);self.assertIn('filtered.map(card)',js);self.assertIn('SURVIVAL FIELD NOTES',new)
 def test_candidate_ledger_retains_names_and_states(self):
  for row in self.catalog['build']['candidateDispositions']:
   self.assertTrue(row.get('candidate'));self.assertTrue(row.get('state'))
 def test_review_counts_and_scores_are_not_conflated(self):
  for g in self.rows:
   self.assertIsInstance(g.get('reviewCount',0),int)
   if not g.get('steamUrl'):self.assertIsNone(g.get('rating'))
   if g.get('reviewCount',0)<30 and g.get('steamUrl') and not g.get('comingSoon'):self.assertLessEqual(score(dict(g,fit=g.get('survivalFit'))) or 0,7)
if __name__=='__main__':unittest.main()
