import csv,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from catalog_model import assemble,score,validate
class MultiPlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.by={g['id']:g for g in cls.catalog['items']}
    def test_originals_preserved(self):
        seeds=list(csv.DictReader((ROOT/'data/seeds.tsv').read_text().splitlines(),delimiter='\t'))
        byseed={str(g.get('seedId')):g for g in self.by.values()}
        self.assertEqual(len(seeds),170)
        for seed in seeds:self.assertIn(seed['appid'],byseed);self.assertIn('Roguelites',byseed[seed['appid']]['hubs'])
    def test_cross_genre_deduplication(self):
        for ident in ['steam:2206270','steam:2747550']:
            self.assertIn('Roguelites',self.by[ident]['hubs']);self.assertIn('Boomer shooters',self.by[ident]['hubs'])
    def test_native_ratings_not_converted(self):
        for g in self.by.values():
            if g.get('externalRating'):
                r=g['externalRating'];self.assertIsNone(g['rating']);self.assertLessEqual(r['value'],r['max']);self.assertGreater(r['count'],0);self.assertTrue(r['sourceUrl'].startswith('https://'))
    def test_support_is_not_a_purchase(self):
        found=0
        for g in self.by.values():
            for s in g.get('storefronts',[]):
                if 'patreon.com/' in s['url']:
                    self.assertEqual(s['kind'],'support');self.assertNotEqual(s['url'],g['primaryUrl']);found+=1
        self.assertGreaterEqual(found,6)
    def test_mod_requirements_and_demos(self):
        self.assertIn('DOOM2.WAD',self.by['external:golden-souls-2']['requirements'])
        self.assertIn('does not require',self.by['external:qbj3']['requirements'])
        self.assertEqual(self.by['external:golden-souls-3']['status'],'Demo')
        self.assertEqual(self.by['external:wanted3d-demo']['status'],'Demo')
        self.assertIn('different products',self.by['external:vietdoom']['curatorWhy'])
    def test_assembly_idempotence(self):
        a=assemble(self.catalog);b=assemble(a)
        self.assertEqual(a['items'],b['items']);self.assertEqual(a['build']['datasetHash'],b['build']['datasetHash'])
    def test_external_score_is_editorial(self):
        g={'verification':'verified','fit':9,'reviewCount':0,'rating':None,'steamUrl':None}
        self.assertEqual(score(g),9);self.assertEqual(score({**g,'confidence':'Exploratory'}),7)
    def test_generated_genre_boundaries(self):
        text=(ROOT/'wiki/Roguelites.md').read_text();self.assertNotIn('Game-3115160-',text)
        self.assertIn('Game-2218750-',text)
        self.assertIn('DOOM2.WAD',(ROOT/'wiki/Game-external-golden-souls-2-Doom-The-Golden-Souls-2.md').read_text())
    def test_official_links_are_safe(self):
        for g in self.by.values():validate(g)
if __name__=='__main__':unittest.main()
