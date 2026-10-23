import importlib.util,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import build
from catalog_model import validate,assemble
class CatalogTests(unittest.TestCase):
    def test_scoring(self):
        g={'verification':'verified','fit':10,'reviewCount':1000,'rating':96,'steamUrl':'https://store.steampowered.com/app/2218750/'}
        self.assertEqual(build.score(g),10)
        self.assertEqual(build.score({**g,'rating':65}),6)
        self.assertEqual(build.score({**g,'rating':45}),5)
        self.assertEqual(build.score({**g,'reviewCount':10}),7)
        self.assertIsNone(build.score({**g,'verification':'unresolved'}))
    def test_canonical_snapshot(self):
        p=ROOT/'data/catalog.json'
        if not p.exists():self.skipTest('Canonical snapshot not present in local fixture test')
        d=json.loads(p.read_text());items=d['items'];self.assertTrue(items)
        self.assertEqual(len(items),len({x['id'] for x in items}))
        self.assertEqual(len(items),d['build']['inputCount'])
        self.assertEqual(d['build']['verifiedCount']+d['build']['unresolvedCount'],len(items))
        for g in items:
            validate(g)
            if g.get('steamUrl'):self.assertRegex(g['steamUrl'],r'^https://store\.steampowered\.com/app/\d+/$')
            else:self.assertTrue(g['id'].startswith('external:'));self.assertIsNone(g.get('rating'))
            if g['verification']=='verified':
                self.assertTrue(g['verifiedAt']);self.assertTrue(g['sources'])
                if g['rating'] is not None:self.assertTrue(0<=g['rating']<=100)
            else:self.assertIsNone(g['rating']);self.assertIsNone(g['fit'])
    def test_build_templates(self):
        html=(ROOT/'site/index.html').read_text();js=(ROOT/'site/app.js').read_text();css=(ROOT/'site/styles.css').read_text()
        for slot in ['/*__CSS__*/','/*__DATA__*/','/*__APP__*/']:self.assertIn(slot,html)
        self.assertIn('prefers-reduced-motion',css);self.assertIn('recommendation(g)',js);self.assertNotIn('eval(',js)
if __name__=='__main__':unittest.main()
