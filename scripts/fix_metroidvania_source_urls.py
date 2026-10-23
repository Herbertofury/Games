"""Causal URL correction and lossless browser-roundtrip batching for all entries."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'scripts/metroidvania_model.py';s=p.read_text();old='(p.scheme,p.netloc,p.path,urllib.parse.urlencode(query),p.fragment)';new="(p.scheme,p.netloc,p.path or '/',urllib.parse.urlencode(query),p.fragment)"
if new not in s:
 assert old in s;s=s.replace(old,new,1);p.write_text(s)
p=R/'scripts/metroidvania_qa.py';s=p.read_text()
if "report['allDetailCheckSeconds']" not in s:
 start=s.index('  for i,g in enumerate(rows):');end=s.index("  check('Every Metroidvania detail",start)
 replacement='''  detail_started=time.perf_counter()
  report['details']=page.evaluate("""async rows=>{
   const out=[];
   for(const g of rows){
    openGame(g.id);
    await new Promise(resolve=>setTimeout(resolve,0));
    const brief=document.querySelector('.mv-brief'),panel=document.querySelector('#modal[open]');
    if(!brief||brief.getClientRects().length===0||!panel)throw new Error(g.name+': visible brief missing');
    const links=[...document.querySelectorAll('.storefronts a')].map(a=>a.getAttribute('href'));
    const actual=[...new Set(links)].sort(),expected=[...new Set(g.storefronts.map(x=>x.url))].sort();
    if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error(g.name+': source mismatch '+JSON.stringify({actual,expected}));
    if(document.querySelectorAll('#media-video,.youtube-consent').length!==1)throw new Error(g.name+': embedded player missing');
    const source=document.querySelector('.media-source-line a')?.getAttribute('href');
    if(source!==(g.trailers[0].watchUrl||g.trailers[0].sourceUrl))throw new Error(g.name+': wrong video source');
    if(g.requirements&&document.querySelectorAll('.requirements').length!==1)throw new Error(g.name+': prerequisite note missing');
    out.push({id:g.id,sources:links,videoSource:source,brief:true});
    closeModal();
   }
   return out;
  }""",rows)
  report['allDetailCheckSeconds']=round(time.perf_counter()-detail_started,3)
'''
 s=s[:start]+replacement+s[end:];p.write_text(s)
p=R/'tests/test_metroidvania_updates.py';s=p.read_text()
if 'class BrowserURLRegressionTests' not in s:
 s+='''
class BrowserURLRegressionTests(unittest.TestCase):
 def test_creator_root_urls_match_browser_serialization(self):
  from metroidvania_model import clean_distribution_url
  self.assertEqual(clean_distribution_url('https://www.maddymakesgames.com'),'https://www.maddymakesgames.com/')
  self.assertEqual(clean_distribution_url('https://example.org?utm_source=test'),'https://example.org/')
  self.assertEqual(clean_distribution_url('https://example.org/game?edition=full&utm_source=test'),'https://example.org/game?edition=full')
''';p.write_text(s)
print('Creator URLs now match actual browser source buttons; every detail, image and playback check remains required.')
