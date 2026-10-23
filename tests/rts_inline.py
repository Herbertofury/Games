"""Offline control smoke only; real network and persistence are proven by rts_qa.py."""
import json,pathlib,shutil
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];rows=[g for g in json.loads((R/'data/catalog.json').read_text())['items'] if 'Real-time strategy' in g.get('hubs',[])];errors=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1536,'height':1100},reduced_motion='reduce');p.route('**/*',lambda r:r.abort());p.on('pageerror',lambda e:errors.append(str(e)));p.set_content((R/'dist/index.html').read_text(),wait_until='domcontentloaded');p.locator('[data-hub="Real-time strategy"]').click();assert p.locator('.game-card').count()==130
 for preset in ['torment','generals','skirmish','free-rts','watchlist','new','demos']:
  p.locator('[data-preset="'+preset+'"]').click();assert p.evaluate('GamesTest.filtered.length')>0,preset
 p.locator('[data-hub="Real-time strategy"]').click()
 proof=p.evaluate('''async rows=>{const out=[];for(const g of rows){openGame(g.id);await new Promise(r=>setTimeout(r,0));const links=[...document.querySelectorAll('.storefronts a')].map(a=>a.href);if(g.storefronts.some(s=>!links.includes(s.url)))throw Error(g.name+' source missing');if(!document.querySelector('.rts-brief'))throw Error(g.name+' brief missing');if(!document.querySelector('.media-source-line a'))throw Error(g.name+' video source missing');out.push(g.id);document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));}return out;}''',rows)
 assert len(proof)==130;assert not errors,errors;p.set_viewport_size({'width':390,'height':844});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1');b.close()
print(json.dumps({'passed':True,'records':len(proof),'errors':errors,'scope':'Offline controls only, not network proof'}))
