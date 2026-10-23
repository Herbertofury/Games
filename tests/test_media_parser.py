import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from collect_external_media import parse,owner_key
class PublisherMedia(unittest.TestCase):
 def test_moddb_excludes_avatars_related_projects_and_game_icons(self):
  x=parse('''<meta property="og:image" content="https://media.moddb.com/images/mods/1/71/70326/logo.png"><div class="body"><img src="https://media.moddb.com/cache/images/mods/1/71/70326/crop_120x90/game.jpg"><img src="https://media.moddb.com/images/members/5/1/2/avatar.png"><img src="https://media.moddb.com/cache/images/mods/1/2/333/crop_120x90/other.jpg"><img src="https://media.moddb.com/images/games/1/1/2/quake.png"></div>''','https://www.moddb.com/mods/test')
  self.assertEqual(len(x['pictures']),1);self.assertIn('game.jpg',x['pictures'][0])
 def test_exact_edition_and_download_identity(self):
  x=parse('''<meta property="og:image" content="https://media.moddb.com/images/downloads/1/237/236512/cut.png"><div class="body"><img src="https://media.moddb.com/cache/images/downloads/1/237/236512/thumb_620x2000/cut.png"><img src="https://media.moddb.com/images/mods/1/26/25250/remake.png"></div>''','https://www.moddb.com/mods/total-chaos/downloads/original')
  self.assertEqual(len(x['pictures']),1);self.assertEqual(owner_key(x['pictures'][0]),'downloads/1/237/236512')
 def test_comments_cannot_supply_trailers(self):
  x=parse('''<meta property="og:image" content="https://img.itch.zone/a.png"><div class="formatted_description"><iframe src="https://www.youtube.com/embed/abcdefghijk"></iframe></div><div id="comments"><iframe src="https://www.youtube.com/embed/notofficial"></iframe></div>''','https://author.itch.io/game')
  self.assertEqual(x['youtube'],['abcdefghijk'])
if __name__=='__main__':unittest.main()
