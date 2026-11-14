"""Preserve the exact Zero Hour mod identity when recovering creator artwork."""
import json
from pathlib import Path
import unittest
R = Path(__file__).resolve().parents[1]
class TEODArtworkTests(unittest.TestCase):
    def test_creator_gallery_artwork_survives_build(self):
        source = next(g for g in json.loads((R/'data/rts-external.json').read_text())['items'] if g['id']=='external:end-of-days-zh')
        built = next(g for g in json.loads((R/'data/catalog.json').read_text())['items'] if g['id']==source['id'])
        self.assertEqual(source['image'], source['screenshots'][0]['src'])
        self.assertTrue(source['image'].endswith('/GLA_-_Fortress.jpg'))
        self.assertNotIn('TEOD_logo.png', source['image'])
        self.assertEqual(source['image'], built['image'])
        self.assertIn('Zero Hour', built['requirements'])
        self.assertEqual(source['primaryUrl'], 'https://www.moddb.com/mods/the-end-of-days')
