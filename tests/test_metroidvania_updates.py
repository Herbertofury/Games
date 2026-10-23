import datetime as dt,pathlib,sys,unittest
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import enrich_metroidvania as collector
class MetroidvaniaRefreshTests(unittest.TestCase):
 def test_creator_media_reuses_fresh_exact_identity(self):
  prior={'id':'external:test','image':'https://example.org/image.png','trailers':[{'youtube':'abcdefghijk'}],'mediaCheckedAt':dt.datetime.now(dt.timezone.utc).isoformat()}
  with patch.object(collector,'page_media',side_effect=AssertionError('Unchanged source must not be reread')):
   self.assertIs(collector.external_phase({'slug':'test'},{'external:test':prior}),prior)
 def test_creator_force_invalidates_fresh_cache(self):
  seed={'slug':'test','name':'Test','url':'https://example.org/game','fit':8,'why':'Test record','scope':'Traditional Metroidvania','free':True}
  prior={'id':'external:test','image':'https://example.org/image.png','trailers':[{'youtube':'abcdefghijk'}],'mediaCheckedAt':dt.datetime.now(dt.timezone.utc).isoformat()}
  source={'sourceUrl':seed['url'],'image':'https://example.org/game.png','pictures':[],'youtube':[]}
  with patch.object(collector,'page_media',return_value=source) as fetch:
   result=collector.external_phase(seed,{'external:test':prior},True)
  self.assertEqual(fetch.call_count,1);self.assertEqual(result['id'],'external:test');self.assertEqual(result['verification'],'verified')
 def test_store_cache_reuse_and_force_are_distinct(self):
  game={'id':'steam:1','name':'Test'};old={'storefronts':[],'storeCoverage':{'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat()}}
  with patch.object(collector.net,'gog',return_value=([],[],None)) as gog,patch.object(collector.net,'owned_site',return_value=([],[],None)):
   ident,result=collector.store_phase(game,old,False);self.assertIs(result,old);self.assertFalse(gog.called)
   ident,result=collector.store_phase(game,old,False,True);self.assertTrue(gog.called);self.assertEqual(ident,game['id']);self.assertIsNot(result,old)
if __name__=='__main__':unittest.main()
