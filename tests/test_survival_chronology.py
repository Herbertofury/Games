import json,pathlib,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class SurvivalChronologyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((R/'data/catalog.json').read_text());cls.by={g['id']:g for g in cls.catalog['items']};cls.dates=json.loads((R/'data/survival-chronology.json').read_text())['overrides'];cls.report=json.loads((R/'data/survival-chronology-report.json').read_text())
 def test_known_old_games_do_not_become_new_by_leaving_early_access(self):
  for ident,early,milestone in [('steam:516750','2016-10-24','2025-01-08'),('steam:387990','2016-01-19','2026-07-24')]:
   g=self.by[ident];self.assertEqual(g['earlyAccessReleaseDate'],early);self.assertEqual(g['releaseDate'],milestone);self.assertEqual(g['originalReleaseYear'],2016);self.assertNotIn('Recent survival release',g['tags'])
 def test_every_confirmed_date_survives_the_overlay(self):
  self.assertGreaterEqual(len(self.dates),2)
  for ident,d in self.dates.items():
   g=self.by[ident];self.assertEqual(g['earlyAccessReleaseDate'],d['earlyAccessReleaseDate']);self.assertLessEqual(g['originalReleaseYear'],int(d['earlyAccessReleaseDate'][:4]));self.assertTrue(g['releaseChronology']['sourceUrl'].startswith('https://store.steampowered.com/app/'))
   if g['originalReleaseYear']<2025:self.assertNotIn('Recent survival release',g['tags'])
 def test_review_coverage_is_reconciled_not_silently_truncated(self):
  self.assertEqual(len(self.report['checks']),self.report['reviewed']);self.assertEqual(len({r['id'] for r in self.report['checks']}),self.report['reviewed']);self.assertEqual(len(self.dates),self.report['confirmedEarlierAccess']);self.assertEqual(sum(r['state']=='unresolved-active' for r in self.report['checks']),len(self.report['unresolved']))
 def test_complete_user_collection_and_media_stay_present(self):
  rows=[g for g in self.catalog['items'] if any(h in g['hubs'] for h in ['Survival','Minecraft-like worlds'])];self.assertGreaterEqual(len(rows),381);self.assertGreaterEqual(len(self.by),1567);self.assertTrue(all(g.get('image') and g.get('trailers') and g.get('storefronts') for g in rows))
if __name__=='__main__':unittest.main()
