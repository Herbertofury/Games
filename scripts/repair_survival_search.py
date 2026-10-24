"""Apply the verified search-contract repair without changing any game records.

Quoted text is a full-text phrase, so Lucid Blocks legitimately matches the
phrase Vintage Story in its comparison note. title: restricts only that token
to names and aliases. Both contracts are tested rather than hiding matches.
"""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED={'site/app.js':'21cc194690a3e3d675d7d27d845e0c62473c3597143bdde57503991e40683070','scripts/survival_qa.py':'3309cc942578aca700867985a91ac8b531b65f96c1bd66914c27cbac1f96a7de'}
AFTER={'site/app.js':'874a82950a7d7a772c38c1e11e6797128078ac3592903ccd15ec8b6c1dfba757','scripts/survival_qa.py':'4b0ba9677b89e13070c658060aaaae7147e4c0e73a680dfa7f57dae0fc40cc93'}
TEST=r'''"""Run the actual JavaScript query matcher against its supported contracts."""
import pathlib, subprocess, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class SearchContractTests(unittest.TestCase):
    def test_real_query_matcher_preserves_full_text_and_adds_title_scope(self):
        source=(ROOT/'site/app.js').read_text()
        function=source.split('function queryMatches(',1)[1].split('function filterGames(',1)[0]
        program=r"""
const assert=require('node:assert/strict');
const prefs={notes:{vintage:'My persistent survival world'}};
const recommendation=g=>g.fit;
const releaseYear=g=>g.releaseDate.slice(0,4);
const base={tags:['Survival','Co-op'],genres:['Adventure'],developers:['Anego Studios'],status:'Early Access',releaseDate:'2016-09-20',collections:['Block worlds'],hubs:['Minecraft-like worlds'],storefronts:[{provider:'Official site'}],kind:'Standalone game',rating:null,reviewCount:0,fit:10};
const vintage={...base,id:'vintage',name:'Vintage Story',seedName:'Vintage Story',aliases:[],_search:'vintage story uncompromising wilderness survival'};
const comparison={...base,id:'lucid',name:'Lucid Blocks',seedName:'Lucid Blocks',aliases:[],_search:'lucid blocks do not assume the tone of minecraft or vintage story'};
const minecraft={...base,id:'minecraft',name:'Minecraft: Java & Bedrock Edition',seedName:'Minecraft',aliases:['Minecraft Java','Minecraft Bedrock'],_search:'minecraft java and bedrock edition minecraft java minecraft bedrock'};
"""+ 'function queryMatches('+function + r"""
assert(queryMatches(vintage,'"Vintage Story"'));
assert(queryMatches(comparison,'"Vintage Story"'), 'Full-text comparisons must remain discoverable');
assert(queryMatches(vintage,'title:"Vintage Story"'));
assert(!queryMatches(comparison,'title:"Vintage Story"'), 'Title scope must not include a description-only match');
assert(queryMatches(minecraft,'title:"Minecraft Java"'));
assert(queryMatches(minecraft,'title:Bedrock'));
assert(queryMatches(vintage,'title:"VINTAGE STORY" score>=9 provider:"Official site"'));
assert(queryMatches(vintage,'"persistent survival"'), 'Private notes remain searchable');
assert(!queryMatches(vintage,'"Vintage Story" -wilderness'));
assert(queryMatches(vintage,'hub:"Minecraft-like worlds" tag:co-op year=2016'));
assert(!queryMatches(vintage,'rating>=80'), 'Missing native ratings must not be fabricated');
assert(queryMatches({...vintage,seedName:null,aliases:null},'title:Vintage'));
assert(queryMatches(vintage,''), 'Empty query retains every record');
console.log('13 source-function search assertions passed');
"""
        p=subprocess.run(['node','-e',program],text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertIn('13 source-function search assertions passed',p.stdout)

if __name__=='__main__':unittest.main()
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 current={n:sha(ROOT/n) for n in EXPECTED}
 if current!=AFTER:
  assert current==EXPECTED,'Source changed since the validated checkpoint; no files changed.'
  p=ROOT/'site/app.js';s=p.read_text()
  old='const c=term.match(/^(tag|genre|developer|status|year|collection|hub|provider|kind):(.*)$/);if(c){const fields={tag:g.tags'
  new='const c=term.match(/^(title|tag|genre|developer|status|year|collection|hub|provider|kind):(.*)$/);if(c){const fields={title:[g.name,g.seedName,...(g.aliases||[])].filter(Boolean),tag:g.tags'
  assert old in s;s=s.replace(old,new,1)
  s=s.replace('fields[c[1]].some(x=>x.toLowerCase().includes(c[2]))','fields[c[1]].some(x=>String(x).toLowerCase().includes(c[2]))',1)
  s=s.replace('Search supports exact phrases, exclusions such as','Search supports exact phrases, title-only queries such as <code>title:&quot;Vintage Story&quot;</code>, exclusions such as',1)
  assert hashlib.sha256(s.encode()).hexdigest()==AFTER['site/app.js']
  q=ROOT/'scripts/survival_qa.py';v=q.read_text()
  old='page.locator(\'[data-hub="Minecraft-like worlds"]\').click();page.locator(\'#search\').fill(\'"Vintage Story"\');check(\'Exact creator-title search\',page.evaluate(\'GamesTest.filtered\')==[\'external:vintage-story\']);page.locator(\'#search\').fill(\'\');page.locator(\'#search\').fill(\'"Minecraft Java"\');check(\'Edition aliases are searchable\',\'external:minecraft\' in page.evaluate(\'GamesTest.filtered\'));page.locator(\'#search\').fill(\'\')'
  new='''page.locator('[data-hub="Minecraft-like worlds"]').click()
  page.locator('#search').fill('"Vintage Story"')
  phrase_results=page.evaluate('GamesTest.filtered')
  expected_phrase=page.evaluate("games.filter(g=>g.hubs.includes('Minecraft-like worlds')&&(g._search+' '+String(prefs.notes[g.id]||'').toLowerCase()).includes('vintage story')).map(g=>g.id)")
  check('Quoted search retains every exact phrase match, including comparison notes',set(phrase_results)==set(expected_phrase) and 'external:vintage-story' in phrase_results)
  page.locator('#search').fill('title:"Vintage Story"')
  check('Title-only search isolates the exact creator game',page.evaluate('GamesTest.filtered')==['external:vintage-story'])
  page.locator('#search').fill('title:"Minecraft Java"')
  check('Title-only search includes edition aliases',page.evaluate('GamesTest.filtered')==['external:minecraft'])
  page.locator('#search').fill('"Minecraft Java"')
  check('Full-text edition aliases remain searchable','external:minecraft' in page.evaluate('GamesTest.filtered'))
  page.locator('#search').fill('')'''
  assert old in v;v=v.replace(old,new,1)
  assert hashlib.sha256(v.encode()).hexdigest()==AFTER['scripts/survival_qa.py']
  p.write_text(s);q.write_text(v)
 test=ROOT/'tests/test_search_contract.py'
 if test.exists():assert test.read_text()==TEST,'Existing regression test differs; preserve it.'
 else:test.write_text(TEST)
 print(json.dumps({'sourceFiles':{n:sha(ROOT/n) for n in EXPECTED},'test':'tests/test_search_contract.py','preserved':'All game IDs, sources, metadata, full-text search, aliases and notes.'},indent=2))
if __name__=='__main__':main()
