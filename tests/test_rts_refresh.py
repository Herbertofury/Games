"""TTL/cache behavior is tested without contacting any provider."""
import datetime as dt,hashlib,json,pathlib,sys,unittest
from unittest.mock import patch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
import enrich_rts
class RTSRefreshTests(unittest.TestCase):
 def test_unchanged_external_snapshot_is_reused(self):
  s=json.loads((R/'data/rts-expansion.json').read_text())['external'][0];ident='external:'+s['slug']
  old={ident:{'id':ident,'seedHash':hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest(),'mediaCheckedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'image':'https://example.org/game.png','trailers':[{'youtube':'abcdefghijk'}]}}
  with patch.object(enrich_rts.media,'fetch',side_effect=AssertionError('Unnecessary request')):
   self.assertIs(enrich_rts.external(s,old),old[ident])
 def test_store_snapshot_is_reused(self):
  g={'id':'steam:1486920'};old={g['id']:{'storeCoverage':{'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat()}}}
  with patch.object(enrich_rts.stores,'gog',side_effect=AssertionError('Unnecessary request')):
   self.assertEqual(enrich_rts.alternate(g,old,'unused'),(g['id'],old[g['id']]))
 def test_explicit_force_refresh_crosses_cache(self):
  g={'id':'steam:1486920','name':'Tempest Rising'};old={g['id']:{'storeCoverage':{'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat()}}}
  with patch.object(enrich_rts.stores,'gog',return_value=([],[],'https://www.gog.com/')) as a,patch.object(enrich_rts.stores,'itch',return_value=([],[],'https://itch.io/')),patch.object(enrich_rts.stores,'owned_site',return_value=([],[],None)):
   enrich_rts.alternate(g,old,'route',force=True);self.assertEqual(a.call_count,1)
if __name__=='__main__':unittest.main()
