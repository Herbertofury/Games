#!/usr/bin/env python3
"""Exercise official-media decoding and on-demand playback in the actual app."""
import contextlib,json,os,pathlib,shutil,socket,subprocess,sys,time
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/'qa';out.mkdir(exist_ok=True)
port=8877;server=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--directory',str(ROOT/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
report={'datasetHash':json.loads((ROOT/'data/catalog.json').read_text())['build']['datasetHash'],'tests':[],'scope':'Five actual streamed trailers across both genres plus portable-file playback. Catalog-wide URL and provenance checks are separate.'}
p=None;browser=None;page=None
try:
    for _ in range(50):
        with contextlib.closing(socket.socket()) as s:
            if s.connect_ex(('127.0.0.1',port))==0:break
        time.sleep(.1)
    p=sync_playwright().start()
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),args=['--no-sandbox'])
    report['browserVersion']=browser.version
    page=browser.new_page(viewport={'width':1536,'height':1100},reduced_motion='reduce')
    page.on('requestfailed',lambda r: report.setdefault('networkFailures',[]).append({'url':r.url,'error':r.failure}))
    page.on('pageerror',lambda e:report.setdefault('pageErrors',[]).append(str(e)))
    page.on('response',lambda r: report.setdefault('streamResponses',[]).append({'url':r.url,'status':r.status}) if any(x in r.url for x in ('.m3u8','.m4s','.ts?','hls.min.js')) else None)
    page.goto(f'http://127.0.0.1:{port}',wait_until='domcontentloaded')
    page.wait_for_function('window.GamesTest && GamesTest.count>0')
    page.wait_for_function('Array.from(document.images).filter(i=>i.naturalWidth>0).length>=3',timeout=45000)
    page.screenshot(path=str(out/'desktop.png'))
    for appid in [2218750,2334730,1942280,2680280,2881610]:
        page.goto(f'http://127.0.0.1:{port}/#game=steam%3A{appid}',wait_until='domcontentloaded')
        page.wait_for_selector('#media-video');page.locator('#media-video').scroll_into_view_if_needed()
        print('Testing official media',appid,flush=True)
        page.wait_for_function('document.querySelector("#media-video").currentSrc.length>0',timeout=45000)
        page.locator('#media-video').evaluate('(v)=>{v.muted=true;v.play().catch(e=>window.__mediaPlayError=String(e))}')
        page.wait_for_function('document.querySelector("#media-video").currentTime>0.5',timeout=30000)
        facts=page.locator('#media-video').evaluate('(v)=>({width:v.videoWidth,height:v.videoHeight,time:v.currentTime,duration:v.duration})')
        assert facts['width']>0 and facts['height']>0
        page.locator('[data-media-mode=screenshots]').click()
        page.wait_for_function('document.querySelector("#media-area .media-stage img")?.naturalWidth>0',timeout=45000)
        image=page.locator('#media-area .media-stage img').evaluate('(i)=>({src:i.currentSrc,width:i.naturalWidth,height:i.naturalHeight})')
        report['tests'].append({'appid':appid,'trailerPlayed':True,'video':facts,'screenshotDecoded':image})
        if appid==2218750:
            page.locator('#modal').evaluate('(e)=>e.scrollTop=0');page.screenshot(path=str(out/'detail.png'))
    page.keyboard.press('Escape');page.set_viewport_size({'width':390,'height':844})
    page.goto(f'http://127.0.0.1:{port}/#hub=Boomer%20shooters',wait_until='domcontentloaded')
    page.locator('.card-image img').first.scroll_into_view_if_needed()
    page.wait_for_function('document.querySelector(".card-image img")?.naturalWidth>0',timeout=30000)
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path=str(out/'mobile.png'))
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.goto((ROOT/'release/Games - Explorer.html').resolve().as_uri()+'#game=steam%3A2218750',wait_until='domcontentloaded')
    page.wait_for_selector('#media-video')
    page.wait_for_function('document.querySelector("#media-video").currentSrc.length>0',timeout=45000)
    page.locator('#media-video').evaluate('(v)=>{v.muted=true;v.play().catch(e=>window.__mediaPlayError=String(e))}')
    page.wait_for_function('document.querySelector("#media-video").currentTime>0.5',timeout=30000)
    report['portableFilePlayback']=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight})')
    assert report['portableFilePlayback']['width']>0
    assert not report.get('pageErrors'),report.get('pageErrors')
    report['passed']=True
except Exception as e:
    report['passed']=False;report['error']=str(e)
    if page:
        try:
            report['videoState']=page.locator('#media-video').evaluate('(v)=>({src:v.currentSrc,readyState:v.readyState,networkState:v.networkState,error:v.error?.message,playError:window.__mediaPlayError})')
        except Exception:pass
        try:page.screenshot(path=str(out/'media-failure.png'))
        except Exception:pass
    raise
finally:
    if browser:browser.close()
    if p:p.stop()
    server.terminate();server.wait(timeout=5)
    (out/'media-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
