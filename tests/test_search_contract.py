"""Run the actual JavaScript query matcher against its supported contracts."""
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
