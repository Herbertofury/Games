"""Run the real shared-model/security tests in the existing source test gate."""
import json,pathlib,subprocess,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class SteamSyncTests(unittest.TestCase):
 def test_node_security_and_snapshot_contract(self):
  result=subprocess.run(['node','--test','--test-reporter=tap','tests/steam-model.test.cjs','services/steam-sync/server.test.mjs','tests/steam-wishlist.test.mjs','tests/steam-extra.test.mjs','tests/steam-refresh.test.cjs'],cwd=R,text=True,capture_output=True,timeout=45)
  self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
  self.assertIn('# fail 0',result.stdout);self.assertIn('# skipped 0',result.stdout)
 def test_static_build_contains_feature_but_no_deployment_claim(self):
  page=(R/'dist/index.html').read_text();config=json.loads((R/'site/steam-config.json').read_text())
  for marker in ['installSteamSync','SteamSyncModel','games.steam.v1','steam-library-strip','steam-sync-panel','installSteamWishlistActions']:
   self.assertIn(marker,page)
  self.assertIn('games.library.v1',page);self.assertIn('games.lounge.v2',page)
  self.assertNotIn('TEST-KEY-NOT-A-REAL-KEY',page)
  self.assertNotIn('GamesSteamApplyWishlist',page)
  if not config['serviceUrl']:self.assertIn('Online sign-in is not configured',page)
 def test_release_packaging_excludes_local_secrets(self):
  import sys
  sys.path.insert(0,str(R/'scripts'));from build import safe_source
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   for name,allowed in [('.env',False),('.env.production',False),('.env.example',True),('signing.key',False),('server.mjs',True)]:
    p=pathlib.Path(d)/name;p.write_text('fixture');self.assertEqual(safe_source(p),allowed,name)
 def test_steam_overlay_does_not_write_original_private_preferences(self):
  source=(R/'site/steam-sync.js').read_text()
  self.assertNotIn('prefs.notes[',source);self.assertNotIn('prefs.favorites=',source)
  self.assertNotIn('localStorage.setItem(KEY',source);self.assertNotIn('sessionStorage.setItem',source)
if __name__=='__main__':unittest.main()
