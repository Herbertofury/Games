"""Keep the verified QBJ3 artwork recovery in the canonical input and build."""
import json
from pathlib import Path
import unittest
R = Path(__file__).resolve().parents[1]

class QBJ3ArtworkTests(unittest.TestCase):
    def test_recovered_project_artwork_survives_build(self):
        source = next(g for g in json.loads((R/'data/shooters-external.json').read_text())['items'] if g['id']=='external:qbj3')
        built = next(g for g in json.loads((R/'data/catalog.json').read_text())['items'] if g['id']=='external:qbj3')
        self.assertIn(source['image'], [x['src'] for x in source['screenshots']])
        self.assertNotIn('qbj3logo_1024x768.png', source['image'])
        self.assertEqual(source['image'], source['trailers'][0]['poster'])
        self.assertEqual(source['image'], built['image'])
        self.assertEqual(source['trailers'][0]['youtube'], built['trailers'][0]['youtube'])
