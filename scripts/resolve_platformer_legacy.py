#!/usr/bin/env python3
"""Observe the exact featured Play Nintendo player's real media request."""
import datetime as dt,hashlib,json,os,pathlib,re,shutil,urllib.parse,urllib.request
from playwright.sync_api import sync_playwright
from resolve_platformer_videos import html_page,PLAY_PAGES
R=pathlib.Path(__file__).resolve().parents[1];Q=R/'qa/platformer-video-resolution';Q.mkdir(parents=True,exist_ok=True)
p=R/'data/platformers-media-reviewed.json';data=json.loads(p.read_text());by={g['id']:g for g in json.loads((R/'data/catalog.json').read_text())['items']};report=[];now=dt.datetime.now(dt.timezone.utc).isoformat()
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox','--autoplay-policy=no-user-gesture-required'])
 for ident,source in PLAY_PAGES.items():
  row={'id':ident,'source':source};ctx=browser.new_context();page=ctx.new_page();requests=[]
  page.on('request',lambda req:requests.append(req.url))
  try:
   soup,proof=html_page(source);public=soup.find('play-video')['data-videoid'];suffix=public.split('/')[-1]
   page.goto(source,wait_until='domcontentloaded');page.wait_for_timeout(2000)
   # Browser locators pierce open shadow roots used by the site player.
   if page.locator('video').count():
    page.locator('video').first.evaluate('(v)=>{v.muted=true;v.play().catch(()=>{});}');page.wait_for_timeout(2000)
   else:
    target=page.locator('play-video').first
    if target.count():target.click(force=True);page.wait_for_timeout(2500)
   row['videoElements']=page.locator('video').evaluate_all('(vs)=>vs.map(v=>({src:v.currentSrc||v.src,html:v.outerHTML}))')
   candidates=[x['src'] for x in row['videoElements'] if x['src'] and not x['src'].startswith('blob:')]
   candidates+= [u for u in requests if suffix in urllib.parse.unquote(u) and re.search(r'\.(mp4|m3u8)(?:\?|$)',u)]
   row['candidates']=list(dict.fromkeys(candidates));row['requests']=[u for u in requests if any(s in u.lower() for s in ['video','cloudinary','m3u8','mp4'])]
   found=None
   for url in row['candidates']:
    host=urllib.parse.urlsplit(url).hostname or ''
    if not (host.endswith('.nintendo.com') or host.endswith('.cloudinary.com')):continue
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Range':'bytes=0-4095'})
    with urllib.request.urlopen(req,timeout=25) as response:head=response.read(4096);mime=response.headers.get('Content-Type','')
    if b'ftyp' in head[:64]:kind='mp4'
    elif head.lstrip().startswith(b'#EXTM3U'):kind='hls'
    else:continue
    found=(url,kind,hashlib.sha256(head).hexdigest());break
   if not found:raise ValueError('Featured player did not expose a validated media stream')
   url,kind,sha=found;video={'name':by[ident]['name']+' — Nintendo trailer',kind:url,'poster':by[ident]['image'],'sourceUrl':source,'watchUrl':source,'official':True,'credit':'Play Nintendo — observed featured video','verified':True,'verifiedAt':now}
   data['overrides'][ident]={'trailers':[video],'sources':[{'provider':'Exact Play Nintendo player','url':source,'verified':True,'lastChecked':now}],'mediaEvidence':{'sourceUrl':source,'publicId':public,'pageEvidence':proof,'observedStream':url,'headerSha256':sha,'checkedAt':now}}
   row['accepted']=True
  except Exception as exc:row['error']=str(exc)
  finally:
   page.screenshot(path=str(Q/(ident.split(':')[1]+'-legacy-player.png')));ctx.close()
  report.append(row);print(json.dumps(row),flush=True)
 browser.close()
data['checkedAt']=now;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');(Q/'legacy-player-report.json').write_text(json.dumps(report,indent=2)+'\n')
