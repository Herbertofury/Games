import json,sys,pathlib,unittest
from unittest.mock import patch
from urllib.parse import urlparse,parse_qs
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import refresh
class ReviewsTests(unittest.TestCase):
    def test_current_api_contract(self):
        url=refresh.reviews_url(2218750)
        self.assertIn('/IUserReviewsService/GetAppReviews/v1/',url)
        args=json.loads(parse_qs(urlparse(url).query)['input_json'][0])
        self.assertEqual(args['languages'],['all']);self.assertEqual(args['purchase_type'],1);self.assertEqual(args['review_type'],0)
    def test_service_envelope(self):
        with patch.object(refresh,'get',return_value={'response':{'query_summary':{'total_reviews':20,'total_positive':19,'total_negative':1}}}):
            self.assertEqual(refresh.reviews_query(1)['total_reviews'],20)
    def test_failure_preserves_known_rating(self):
        g={'appid':1,'verification':'verified','rating':95.3,'reviewCount':1000,'warnings':[]}
        with patch.object(refresh,'reviews_query',side_effect=ValueError('offline')):refresh.repair_reviews(g)
        self.assertEqual(g['rating'],95.3);self.assertEqual(g['reviewCount'],1000);self.assertEqual(g['reviewError'],'offline')
    def test_real_catalog_has_review_evidence(self):
        games=json.loads((ROOT/'data/catalog.json').read_text())['items']
        halls=next(g for g in games if g['appid']==2218750)
        self.assertIsNotNone(halls.get('rating'));self.assertGreater(halls['reviewCount'],1000)
        self.assertFalse([g['name'] for g in games if g.get('verification')=='verified' and g.get('reviewError')])
if __name__=='__main__':unittest.main()
