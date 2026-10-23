#!/usr/bin/env python3
"""Bounded differential media diagnostics; never substitutes for final app QA."""
import asyncio,json,pathlib,os,shutil,subprocess,sys,urllib.request
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
async def main():
    out=ROOT/'qa';out.mkdir(exist_ok=True)
    d=json.loads((ROOT/'data/catalog.json').read_text());g=next(g for g in d['items'] if g['appid']==2218750);url=g['trailers'][0]['hls']
    report={'url':url,'cases':[]}
    try:
        with urllib.request.urlopen(url,timeout=20) as r:report['manifest']={'status':r.status,'headers':dict(r.headers),'body':r.read().decode()}
    except Exception as e:report['manifestError']=str(e)
    (ROOT/'dist/probe.html').write_text('<!doctype html><title>Media diagnostic</title><video id="v" controls muted playsinline></video>')
    server=subprocess.Popen([sys.executable,'-m','http.server','8878','--directory',str(ROOT/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        await asyncio.sleep(.5)
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox'])
            async def case(name,version,config,order):
                page=await browser.new_page();events=[];network=[]
                page.on('console',lambda m:events.append({'console':m.type,'text':m.text}))
                page.on('pageerror',lambda e:events.append({'pageError':str(e)}))
                page.on('requestfailed',lambda r:network.append({'url':r.url,'failure':r.failure}))
                await page.goto('http://127.0.0.1:8878/probe.html')
                await page.add_script_tag(url=f'https://cdn.jsdelivr.net/npm/hls.js@{version}/dist/hls.min.js')
                await page.evaluate('''({url,config,order})=>{
                  const v=document.querySelector('video');window.events=[];window.player=new Hls({...config,debug:true});
                  for(const event of [Hls.Events.MEDIA_ATTACHED,Hls.Events.MANIFEST_LOADED,Hls.Events.MANIFEST_PARSED,Hls.Events.LEVEL_LOADED,Hls.Events.ERROR]) player.on(event,(_,e)=>events.push({event,details:typeof e.details==='string'?e.details:undefined,type:e.type,fatal:e.fatal,error:String(e.error||''),levels:e.levels?.length}));
                  if(order==='attached'){player.on(Hls.Events.MEDIA_ATTACHED,()=>player.loadSource(url));player.attachMedia(v);}
                  else {player.loadSource(url);player.attachMedia(v);}
                  v.play().catch(e=>events.push({playError:String(e)}));
                }''',{'url':url,'config':config,'order':order})
                result={'name':name,'version':version,'config':config,'order':order}
                try:
                    await page.wait_for_function('document.querySelector("video").currentTime>.5',timeout=20000);result['played']=True
                except Exception as e:result['played']=False;result['error']=str(e)
                result['state']=await page.evaluate('''()=>({events:window.events,time:document.querySelector('video').currentTime,ready:document.querySelector('video').readyState,levelCount:player.levels.length,loading:player.loadingEnabled,mediaSource:player.mediaSource?.readyState,capabilities:typeof navigator.mediaCapabilities?.decodingInfo})''')
                result['console']=events;result['networkFailures']=network
                report['cases'].append(result);print(name,result['played'],flush=True);await page.close()
            await asyncio.gather(case('current','1.7.3',{},'source-first'),case('attached-first','1.7.3',{},'attached'),case('bounded-capabilities','1.7.3',{'useMediaCapabilities':False},'attached'),case('prior-stable-control','1.6.19',{},'attached'))
            await browser.close()
    finally:
        server.terminate();server.wait(timeout=5);(ROOT/'dist/probe.html').unlink(missing_ok=True)
        (out/'media-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
asyncio.run(main())
