"""Offline inline smoke for every source panel; does not claim network playback proof."""
import json,pathlib
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];rows=[g for g in json.loads((R/'data/catalog.json').read_text())['items'] if 'Boomer shooters' in g['hubs']]
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=b.new_page(viewport={'width':1536,'height':1100},reduced_motion='reduce');p.route('**/*',lambda route:route.abort());errs=[];p.on('pageerror',lambda e:errs.append(str(e)));p.set_content((R/'dist/index.html').read_text(),wait_until='domcontentloaded');p.locator('[data-hub="Boomer shooters"]').click();assert p.locator('.card-source-summary').count()==len(rows)
 proof=p.evaluate("""async rows=>{const out=[];for(const g of rows){openGame(g.id);document.querySelector('[data-media-mode=trailer]').click();await new Promise(r=>setTimeout(r,0));const hrefs=Array.from(document.querySelectorAll('.storefronts a')).map(a=>a.href);const expected=g.storefronts.map(x=>x.url);if(hrefs.length!==expected.length||expected.some(x=>!hrefs.includes(x)))throw Error(g.name+' store mismatch');if(document.querySelectorAll('.media-source-line a').length!==1)throw Error(g.name+' source missing');if(document.querySelectorAll('#media-video,.youtube-consent').length!==1)throw Error(g.name+' player missing');out.push(g.id);document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));}return out;}""",rows)
 assert len(proof)==len(rows)
 p.evaluate("openGame('external:death-wish')");assert 'adaptation' in p.locator('.media-edition-note').inner_text();p.keyboard.press('Escape');assert not errs,errs
 print(json.dumps({'scope':'Offline inline controls only','detailsChecked':len(rows),'errors':errs,'passed':True}));b.close()
