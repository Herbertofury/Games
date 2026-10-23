#!/usr/bin/env python3
"""Read-only diagnosis of the two observed Nintendo legacy video streams."""
import json,os,pathlib,shutil,subprocess,time,urllib.request
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa';Q.mkdir(exist_ok=True)
media=json.loads((R/'data/platformers-media-reviewed.json').read_text())['overrides'];report=[]
server=subprocess.Popen(['python3','-m','http.server','8790','--directory',str(R/'dist')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.5)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
  for ident in ['external:super-mario-odyssey','external:super-mario-maker-2']:
   v=media[ident]['trailers'][0];url=v['hls'];row={'id':ident,'hls':url,'network':[],'console':[],'errors':[],'candidates':[]}
   try:
    with urllib.request.urlopen(url,timeout=20) as response:row['playlist']=response.read(100000).decode();row['headers']=dict(response.headers)
   except Exception as exc:row['playlistError']=str(exc)
   page=browser.new_page();page.on('console',lambda m:row['console'].append(m.text));page.on('requestfailed',lambda req:row['network'].append({'url':req.url,'failure':req.failure}));page.on('response',lambda resp:row['network'].append({'url':resp.url,'status':resp.status}) if resp.status>=400 else None)
   page.goto('http://127.0.0.1:8790/#hub=Platformers',wait_until='domcontentloaded');page.wait_for_function('window.GamesTest');page.evaluate('(id)=>openGame(id)',ident);page.wait_for_timeout(3000)
   page.evaluate('window.hlsDiagnostics=[];if(hls)hls.on(Hls.Events.ERROR,(_,e)=>hlsDiagnostics.push({type:e.type,details:e.details,fatal:e.fatal,error:String(e.error),url:e.url,response:e.response}));')
   page.locator('#media-video').evaluate('(v)=>{v.muted=true;v.play().catch(e=>window.playError=String(e));}');page.wait_for_timeout(10000)
   row['video']=page.locator('#media-video').evaluate('(v)=>({time:v.currentTime,readyState:v.readyState,networkState:v.networkState,width:v.videoWidth,src:v.currentSrc,error:v.error?{code:v.error.code,message:v.error.message}:null})')
   row['hlsErrors']=page.evaluate('window.hlsDiagnostics');row['playError']=page.evaluate('window.playError||null');page.screenshot(path=str(Q/(ident.split(':')[1]+'-stream-diagnostic.png')));page.close()
   # These are public progressive encodings of the exact observed public ID,
   # not accepted metadata until real MP4 bytes AND native playback succeed.
   prefix=url.split('/video/upload/')[0]+'/video/upload/'
   asset=url.split('/v1/',1)[1].split('.m3u8')[0]
   for transform in ['f_mp4,q_auto','f_mp4','']:
    candidate=prefix+(transform+'/' if transform else '')+'v1/'+asset+'.mp4'
    probe={'url':candidate}
    try:
     req=urllib.request.Request(candidate,headers={'User-Agent':'Mozilla/5.0','Range':'bytes=0-4095'})
     with urllib.request.urlopen(req,timeout=20) as response:head=response.read(4096);probe.update(status=response.status,contentType=response.headers.get('Content-Type'),mp4=b'ftyp' in head[:64])
    except Exception as exc:probe['error']=str(exc)
    row['candidates'].append(probe)
   report.append(row);print(json.dumps(row),flush=True)
  browser.close()
finally:
 server.terminate();server.wait(timeout=5);(Q/'platformer-stream-diagnostics.json').write_text(json.dumps(report,indent=2)+'\n')
