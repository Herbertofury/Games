#!/usr/bin/env python3
"""Record actual public browser builds; never label library captures official.

Captures remain proposed until screenshots are visually reviewed. No member-
only content, native executable, ROM substitution or generated imagery is used.
This is a short functionality preview, not a full playtest or completion claim.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,shutil,urllib.request
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];OUT=R/'qa/platformer-video-resolution';OUT.mkdir(parents=True,exist_ok=True)
DEST=R/'site/assets/platformer-previews';DEST.mkdir(parents=True,exist_ok=True)
GAMES=[('external:celeste-classic','CELESTE Classic','https://maddymakesgamesinc.itch.io/celesteclassic','https://html-classic.itch.zone/html/235259/Celeste/index.html'),('external:celeste-classic-2',"Celeste Classic 2: Lani's Trek",'https://maddymakesgamesinc.itch.io/celeste-classic-2','https://html-classic.itch.zone/html/3276960/index.html')]
report=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
    for ident,name,source,build in GAMES:
        row={'id':ident,'name':name,'sourceUrl':source,'buildUrl':build,'reviewState':'Pending visual inspection; do not publish automatically'};ctx=None;key=ident.split(':')[1]
        try:
            req=urllib.request.Request(source,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=30) as response:raw=response.read(3000000)
            soup=BeautifulSoup(raw,'html.parser');iframes=[x.get('src') or x.get('data-src') for x in soup.find_all('iframe')]
            assert build in iframes or build in raw.decode('utf-8'),'Creator page does not link the exact browser build'
            row['sourcePageSha256']=hashlib.sha256(raw).hexdigest()
            ctx=browser.new_context(viewport={'width':640,'height':640},record_video_dir=str(OUT/'raw'),record_video_size={'width':640,'height':640})
            page=ctx.new_page();page.goto(build,wait_until='domcontentloaded');page.wait_for_timeout(1500)
            (OUT/(key+'-initial.html')).write_text(page.content())
            start=page.locator('#p8_start_button')
            if start.count() and start.is_visible():start.click(force=True)
            else:page.mouse.click(320,260)
            canvas=page.locator('canvas').first;canvas.wait_for(state='visible',timeout=30000);canvas.click(force=True);page.wait_for_timeout(1800)
            # Both original title screens require X+C together, not two
            # successive taps. Hold long enough to span real animation frames.
            page.keyboard.down('x');page.keyboard.down('c');page.wait_for_timeout(350);page.keyboard.up('c');page.keyboard.up('x');page.wait_for_timeout(1700)
            page.screenshot(path=str(OUT/(key+'-start.png')))
            for i in range(16):
                direction='ArrowRight' if i%6<4 else 'ArrowLeft';page.keyboard.down(direction);page.keyboard.down('x');page.wait_for_timeout(180);page.keyboard.up('x');page.wait_for_timeout(200);page.keyboard.press('c');page.wait_for_timeout(240);page.keyboard.up(direction);page.wait_for_timeout(160)
            page.screenshot(path=str(OUT/(key+'-motion.png')))
            for i in range(8):
                page.keyboard.down('ArrowRight');page.keyboard.down('x');page.wait_for_timeout(180);page.keyboard.up('x');page.wait_for_timeout(160);page.keyboard.press('c');page.wait_for_timeout(220);page.keyboard.up('ArrowRight')
            page.screenshot(path=str(OUT/(key+'-end.png')));video=page.video
            ctx.close();ctx=None;rawpath=pathlib.Path(video.path());target=DEST/(key+'.webm');shutil.copyfile(rawpath,target)
            # Validate the browser's WebM output with a separate native player;
            # no system ffmpeg or re-encoding is required for this evidence.
            review=browser.new_context();probe=review.new_page();probe.goto(target.as_uri(),wait_until='domcontentloaded');probe.wait_for_function('document.querySelector("video")?.readyState>=1',timeout=20000)
            info=probe.locator('video').evaluate('(v)=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight})');review.close()
            assert info['duration']>8 and info['width']>0,'Invalid or too-short recording'
            row.update(localPath=str(target.relative_to(R)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size,videoInfo=info)
        except Exception as exc:
            row['error']=str(exc)
            if ctx:
                try:page.screenshot(path=str(OUT/(key+'-failure.png')));(OUT/(key+'-failure.html')).write_text(page.content())
                except Exception:pass
        finally:
            if ctx:ctx.close()
        report.append(row);print(json.dumps(row),flush=True)
    browser.close()
(OUT/'browser-preview-proposals.json').write_text(json.dumps(report,indent=2)+'\n')
