"""Completion invariants protect identities while filling the known media gaps."""
import copy,hashlib,json,pathlib,sys,unittest,urllib.parse
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from platformer_media import apply_reviewed_media
from platformer_study import has_video

class PlatformerCompletionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((R/'data/catalog.json').read_text());cls.rows=[g for g in cls.catalog['items'] if 'Platformers' in g.get('hubs',[])];cls.by={g['id']:g for g in cls.rows};cls.overlay=json.loads((R/'data/platformers-media-reviewed.json').read_text());cls.raw={g['id']:g for f in ['platformers-steam.json','platformers-external.json'] for g in json.loads((R/'data'/f).read_text())['items']}
 def test_all_platformer_media_complete(self):
  self.assertEqual(len(self.rows),439)
  self.assertTrue(all(g.get('image') and has_video(g) for g in self.rows))
  report=json.loads((R/'data/platformers-study-report.json').read_text())
  self.assertEqual(report['withPlayableVideoMetadata'],439);self.assertFalse(report['mediaGaps'])
 def test_twenty_previously_missing_sources_are_resolved(self):
  self.assertEqual(len(self.overlay['overrides']),20)
  self.assertLessEqual(set(self.overlay['overrides']),set(self.by))
 def test_overlay_cannot_change_game_facts(self):
  for ident,extra in self.overlay['overrides'].items():
   original=copy.deepcopy(self.raw[ident]);result=apply_reviewed_media(original,extra)
   for key in original:
    if key not in ['trailers','sources','warnings']:self.assertEqual(result[key],original[key],(ident,key))
   self.assertEqual(original,self.raw[ident]);self.assertEqual(result,apply_reviewed_media(result,extra))
  with self.assertRaises(AssertionError):apply_reviewed_media(self.raw['steam:227600'],{'rating':100})
 def test_nonofficial_captures_are_never_labelled_trailers(self):
  for ident,extra in self.overlay['overrides'].items():
   for video in extra['trailers']:
    self.assertTrue(video['verified']);self.assertTrue(video['credit']);self.assertTrue(video['sourceUrl'].startswith('https://'))
    if ident in ['external:celeste-classic','external:celeste-classic-2']:
     self.assertFalse(video['official']);self.assertEqual(video['captureKind'],'Library-captured public browser preview');self.assertIn('preview',video['name'].lower())
    if ident=='external:celeste-64':self.assertFalse(video['official']);self.assertIn('GIGAZINE',video['credit'])
 def test_browser_preview_bytes_match_reviewed_hash(self):
  for ident in ['external:celeste-classic','external:celeste-classic-2']:
   video=self.overlay['overrides'][ident]['trailers'][0];local=R/video['capturePath']
   self.assertTrue(local.is_file());self.assertEqual(hashlib.sha256(local.read_bytes()).hexdigest(),video['captureSha256'])
   self.assertRegex(video['webm'],r'^https://raw\.githubusercontent\.com/Herbertofury/Games/[0-9a-f]{40}/site/assets/platformer-previews/')
 def test_nintendo_video_matches_exact_product_not_recommendations(self):
  for ident,extra in self.overlay['overrides'].items():
   proof=extra.get('mediaEvidence',{})
   if proof.get('sku'):
    slug=urllib.parse.urlsplit(self.by[ident]['primaryUrl']).path.strip('/').split('/')[-1]
    self.assertEqual(proof['urlKey'],slug)
    self.assertEqual(proof['probe']['status'],206)
    self.assertIn(proof['publicId'].lstrip('/'),extra['trailers'][0]['mp4'])
 def test_watchlist_still_not_a_purchase_recommendation(self):
  g=self.by['steam:2661310'];self.assertTrue(g['comingSoon']);self.assertIsNone(g['fit'])
  self.assertIn('historical',self.overlay['overrides'][g['id']]['trailers'][0]['editionNote'])
 def test_primary_routes_do_not_mutate_shared_genre_membership(self):
  self.assertEqual(len({g['platformerCollection'] for g in self.rows}),10)
  for aid in [1170060,1836730,1933000]:self.assertIn('Boomer shooters',self.by['steam:'+str(aid)]['hubs'])
  js=(R/'site/platformers.js').read_text();self.assertIn('collections:[g.platformerCollection]',js);self.assertIn('primaryRoutesKey',js)

if __name__=='__main__':unittest.main()
