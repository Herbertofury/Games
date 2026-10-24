import json,pathlib,subprocess,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class LoungeTests(unittest.TestCase):
 def test_exact_catalog_is_preserved(self):
  c=json.loads((R/'data/catalog.json').read_text());self.assertEqual(len(c['items']),1853);self.assertEqual(c['build']['datasetHash'],'b2571a5892d17b23994477080f616e64d9177ae78344e99bdfe9407b87063cbb');self.assertEqual(len({g['id'] for g in c['items']}),1853)
 def test_all_old_genres_are_intact(self):
  c=json.loads((R/'data/catalog.json').read_text());self.assertEqual(c['build']['hubCounts'],{'Boomer shooters':150,'Couch co-op & party':339,'Metroidvanias':430,'Minecraft-like worlds':82,'Platformers':439,'Real-time strategy':130,'Roguelites':198,'Survival':299})
 def test_number_formatter_equivalence(self):
  js="const a=new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1});for(const n of [0,null,1,12,999,1000,1234,15350,1e6,2e9,-10]){const old=new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:1}).format(n||0);if(old!==a.format(n||0))throw Error(n);}"
  subprocess.run(['node','-e',js],check=True)
 def test_native_game_and_presentation_are_packaged(self):
  h=(R/'dist/index.html').read_text();self.assertIn('installDesktopArcade',h);self.assertIn('installLounge',h);self.assertIn('SNACKBALL.exe',h);self.assertNotIn('/*__APP__*/',h)
 def test_storage_namespaces_are_preserved(self):
  self.assertIn("const KEY='games.library.v1'",(R/'site/app.js').read_text());self.assertIn('games.lounge.v2',(R/'site/lounge.js').read_text());self.assertIn('games.snackball.v1',(R/'site/arcade.js').read_text())
 def test_no_remote_arcade_dependencies(self):
  text=(R/'site/arcade.js').read_text();self.assertNotIn('https://',text);self.assertNotIn('fetch(',text);self.assertNotIn('eval(',text)
 def test_complete_render_remains(self):self.assertIn('filtered.map(card)',(R/'site/app.js').read_text())
 def test_new_wiki_page_is_present(self):self.assertTrue((R/'wiki/Games-Lounge.md').exists());self.assertIn('Games-Lounge',(R/'wiki/_Sidebar.md').read_text())
if __name__=='__main__':unittest.main()
