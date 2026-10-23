"""Acceptance invariants for the complete platformer source set, not a sample."""
import csv,json,pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble,game_key,score,validate
from collect_platformers import accepted
from platformer_study import has_video

class PlatformerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((R/'data/catalog.json').read_text());cls.by={g['id']:g for g in cls.data['items']};cls.rows=[g for g in cls.by.values() if 'Platformers' in g.get('hubs',[])];cls.steam=json.loads((R/'data/platformers-steam.json').read_text());cls.external=json.loads((R/'data/platformers-external.json').read_text());cls.report=json.loads((R/'data/platformers-study-report.json').read_text())
 def test_complete_source_union_no_duplicates(self):
  expected={'steam:'+s['appid'] for s in csv.DictReader((R/'data/seeds.tsv').open(),delimiter='\t')}
  for file in ['shooters-steam.json','shooters-external.json','rts-steam.json','rts-external.json','platformers-steam.json','platformers-external.json']:
   expected.update(g['id'] for g in json.loads((R/'data'/file).read_text())['items'])
  self.assertEqual(expected,set(self.by));self.assertEqual(len(self.by),len(self.data['items']))
  self.assertEqual(self.data['build']['inputCount'],len(self.by))
 def test_all_discovery_candidates_reconciled(self):
  seeds=list(csv.DictReader((R/'data/platformers-seeds.tsv').open(),delimiter='\t'));self.assertGreaterEqual(len(seeds),420)
  self.assertFalse(self.steam['unresolved']);self.assertEqual(len(seeds),len(self.steam['items']))
  byname={g['seedName']:g for g in self.steam['items']}
  for seed in seeds:
   g=byname[seed['name']];self.assertTrue(accepted(seed,g['name']));self.assertEqual(int(seed['appid']),g['appid'])
 def test_exact_platformer_membership(self):
  self.assertEqual({g['id'] for g in self.rows},{g['id'] for g in self.steam['items']+self.external['items']})
  self.assertGreaterEqual(len(self.rows),439);self.assertEqual(len(self.external['items']),19)
  self.assertEqual(len({g['platformerCollection'] for g in self.rows}),10)
 def test_original_hubs_and_hades_preserved(self):
  self.assertEqual(sum('Boomer shooters' in g.get('hubs',[]) for g in self.by.values()),150)
  self.assertEqual(sum('Real-time strategy' in g.get('hubs',[]) for g in self.by.values()),130)
  self.assertIn('Roguelites',self.by['steam:1145360']['hubs'])
  for seed in csv.DictReader((R/'data/seeds.tsv').open(),delimiter='\t'):self.assertIn('Roguelites',self.by['steam:'+seed['appid']]['hubs'])
 def test_cross_genre_identity_is_shared(self):
  for aid in [1170060,1836730,1933000]:
   g=self.by['steam:'+str(aid)];self.assertIn('Platformers',g['hubs']);self.assertIn('Boomer shooters',g['hubs']);self.assertNotIn('platformerManaged',g)
  for g in self.rows:
   if g['platformerCollection']=='Roguelite platformers':self.assertIn('Roguelites',g['hubs'])
 def test_renames_and_wrong_editions_are_not_duplicates(self):
  self.assertEqual(self.by['steam:1221480']['seedName'],'Big Hops');self.assertIn('Together',self.by['steam:1221480']['name'])
  self.assertEqual(self.by['steam:2313700']['seedName'],'Constance');self.assertNotIn('steam:3351070',self.by)
  self.assertEqual(self.by['steam:1038300']['seedName'],"New Super Lucky's Tale")
  self.assertIn('LOVE 2',self.by['steam:578930']['name'])
 def test_verified_records_have_real_sources(self):
  for g in self.rows:
   with self.subTest(game=g['name']):
    validate(g);self.assertEqual(g['verification'],'verified');self.assertTrue(g.get('verifiedAt'));self.assertTrue(g.get('sources'));self.assertTrue(g.get('storefronts'))
    for s in g['sources']:self.assertTrue(s['url'].startswith('https://'))
    if g.get('steamUrl'):self.assertTrue(g['image']);self.assertEqual(g['steamUrl'],f"https://store.steampowered.com/app/{g['appid']}/")
 def test_upcoming_and_small_samples_are_not_oversold(self):
  upcoming=[g for g in self.rows if g.get('comingSoon')];self.assertTrue(upcoming)
  for g in upcoming:self.assertIsNone(g.get('fit'));self.assertIsNone(score(g));self.assertFalse(g.get('hiddenGem'))
  for g in self.rows:
   if g.get('steamUrl') and g.get('reviewCount',0)<30 and score(g) is not None:self.assertLessEqual(score(g),7)
 def test_console_hardware_and_native_ratings_are_explicit(self):
  for g in self.external['items']:self.assertIsNone(g['rating']);self.assertFalse(g.get('steamUrl'));self.assertTrue(g['platforms']);self.assertTrue(g['requirements'])
  for ident in ['external:donkey-kong-bananza','external:yoshi-mysterious-book','external:kirby-forgotten-land']:self.assertIn('Nintendo Switch 2',self.by[ident]['platforms'])
  self.assertIn('PlayStation 5',self.by['external:astro-bot']['platforms'])
 def test_hybrids_are_not_silently_relabelled(self):
  for ident in ['steam:2394650','steam:881100','steam:400','steam:1836730']:
   self.assertIn('hybrid',self.by[ident]['platformerInfo']['scope'].lower())
  self.assertIn('top-down',self.by['steam:2394650']['platformerInfo']['focus'].lower())
 def test_gem_shortlist_obeys_published_rule(self):
  gems=[g for g in self.rows if 'Platformer gem shortlist' in g['tags']];self.assertTrue(gems)
  for g in gems:self.assertTrue(g['hiddenGem']);self.assertGreaterEqual(g['rating'],80);self.assertTrue(30<=g['reviewCount']<=5000);self.assertGreaterEqual(score(g),8);self.assertFalse(g.get('comingSoon'))
 def test_every_dossier_and_atlas_entry_exists(self):
  atlas=(R/'wiki/Platformers-Media.md').read_text();index=(R/'wiki/Platformers.md').read_text()
  for g in self.rows:
   key=game_key(g);self.assertIn(key,atlas);self.assertIn(key,index);text=(R/'wiki'/(key+'.md')).read_text();self.assertIn('## Platformer field notes',text);self.assertIn('[Platformers](Platformers)',text);self.assertIn(g.get('primaryUrl') or g['steamUrl'],atlas)
 def test_coverage_counts_do_not_hide_media_gaps(self):
  self.assertEqual(self.report['records'],len(self.rows));self.assertEqual(self.report['withArtwork'],sum(bool(g.get('image')) for g in self.rows));self.assertEqual(self.report['withPlayableVideoMetadata'],sum(has_video(g) for g in self.rows))
  expected={g['id'] for g in self.rows if not g.get('image') or not has_video(g)};self.assertEqual(expected,{g['id'] for g in self.report['mediaGaps']})
  self.assertGreaterEqual(self.report['individualEditorialNotes'],120)
 def test_build_is_idempotent(self):
  again=assemble(self.data);self.assertEqual(self.data['items'],again['items']);self.assertEqual(self.data['build']['datasetHash'],again['build']['datasetHash'])
 def test_existing_persistence_key_and_integrated_sources(self):
  app=(R/'site/app.js').read_text();page=(R/'dist/index.html').read_text()
  self.assertIn('games.library.v1',app);self.assertIn('installPlatformerHub',page);self.assertIn('platformer-guide',page);self.assertNotIn('/*__APP__*/',page)
 def test_source_refresh_handles_nonsteam_records(self):
  refresh=(R/'scripts/refresh.py').read_text();self.assertNotIn("old={str(g['seedId']):g",refresh)

if __name__=='__main__':unittest.main()
