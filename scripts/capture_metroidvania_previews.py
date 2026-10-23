"""Capture public freeware/demo builds in an isolated disposable CI runner.
No purchases, login, paid downloads, or claims of a full game review.
The recorder retains source URL, exact downloaded hash, process logs and frames.
"""
import argparse,hashlib,json,os,pathlib,shutil,signal,subprocess,tarfile,time,zipfile
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1]
CONFIG={
 'spellsought':{'url':'https://speedrockstrong.itch.io/spellsought','upload':'19262155','platform':'windows','title':'Spellsought v1.0.3'},
 'reawakening':{'url':'https://hatbird-games.itch.io/reawakening','platform':'linux','title':'Reawakening public Linux build'},
 'mongrel-story':{'url':'https://mountainstork.itch.io/mongrel-story-demo','upload':'14164878','platform':'linux','title':'Mongrel Story public demo v0.8.0'}
}
def run(cmd,**kwargs):return subprocess.run(cmd,check=True,**kwargs)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('game',choices=CONFIG);a=ap.parse_args();c=CONFIG[a.game]
 out=R/'qa'/('capture-'+a.game);out.mkdir(parents=True,exist_ok=True);work=pathlib.Path('/tmp/mv-preview')/a.game;work.mkdir(parents=True,exist_ok=True)
 report={'id':'external:'+a.game,'sourceUrl':c['url'],'build':c['title'],'type':'Catalog-recorded public build preview','reviewClaim':'Short preview only, not a completed playthrough or hands-on review.'}
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);ctx=browser.new_context(accept_downloads=True);p=ctx.new_page();p.goto(c['url'],wait_until='domcontentloaded',timeout=45000)
   if c.get('upload'):
    with p.expect_download(timeout=60000) as dl:p.locator('[data-upload_id="'+c['upload']+'"]').click()
   else:
    p.locator('.buy_btn').first.click();p.get_by_text('No thanks, just take me to the downloads',exact=False).click();p.wait_for_selector('.download_btn')
    uploads=p.locator('.upload');chosen=None
    for i in range(uploads.count()):
     u=uploads.nth(i)
     if 'linux' in u.inner_text().lower() or u.locator('.icon-tux').count():chosen=u;break
    if chosen is None:raise RuntimeError('The creator page did not expose the public Linux build')
    with p.expect_download(timeout=60000) as dl:chosen.locator('.download_btn').click()
   download=dl.value;dest=work/download.suggested_filename;download.save_as(str(dest));report.update(filename=dest.name,bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest());p.screenshot(path=str(out/'download-source.png'));browser.close()
  unpack=work/'game';unpack.mkdir(exist_ok=True)
  if zipfile.is_zipfile(dest):
   with zipfile.ZipFile(dest) as z:
    assert all(not pathlib.PurePosixPath(n).is_absolute() and '..' not in pathlib.PurePosixPath(n).parts for n in z.namelist());z.extractall(unpack)
  elif tarfile.is_tarfile(dest):
   with tarfile.open(dest) as t:t.extractall(unpack,filter='data')
  else:raise RuntimeError('Unsupported creator archive')
  report['files']=[str(p.relative_to(unpack)) for p in unpack.rglob('*') if p.is_file()]
  env=dict(os.environ,DISPLAY=':97',LIBGL_ALWAYS_SOFTWARE='1',WINEDEBUG='-all',WINEPREFIX=str(work/'wine'),HOME=str(work/'home'))
  pathlib.Path(env['HOME']).mkdir(exist_ok=True)
  xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','1280x720x24','-nolisten','tcp'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
  if c['platform']=='windows':
   exes=[p for p in unpack.rglob('*.exe') if 'console' not in p.name.lower() and 'crash' not in p.name.lower()]
   if len(exes)!=1:raise RuntimeError('Ambiguous executable selection: '+str(exes))
   exe=exes[0];wine=shutil.which('wine64') or '/usr/lib/wine/wine64';cmd=[wine,str(exe),'--rendering-method','gl_compatibility','--rendering-driver','opengl3','--resolution','1280x720','--position','0,0']
  else:
   exes=[]
   for p in unpack.rglob('*'):
    if not p.is_file() or p.suffix in ['.so','.pck']:continue
    with p.open('rb') as f:head=f.read(4)
    if head==b'\x7fELF' and not any(x in p.name.lower() for x in ['crash','unityplayer']):exes.append(p)
   if len(exes)!=1:raise RuntimeError('Ambiguous native executable selection: '+str(exes))
   exe=exes[0];exe.chmod(0o755);cmd=[str(exe),'--rendering-method','gl_compatibility','--rendering-driver','opengl3','--resolution','1280x720','--position','0,0','-screen-width','1280','-screen-height','720','-screen-fullscreen','0']
  log=(out/'game.log').open('w');proc=subprocess.Popen(cmd,cwd=exe.parent,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);report['executable']=str(exe.relative_to(unpack));time.sleep(10)
  if proc.poll() is not None:raise RuntimeError('Public build exited before preview capture; inspect game.log')
  def key(*keys):subprocess.run(['xdotool','key','--clearmodifiers',*keys],env=env,check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  def screenshot(name):run(['ffmpeg','-loglevel','error','-f','x11grab','-video_size','1280x720','-i',':97','-frames:v','1',str(out/name)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  screenshot('before.png');key('Return');time.sleep(2);key('space');time.sleep(2);key('Return');time.sleep(2);screenshot('start.png')
  cap=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','x11grab','-framerate','30','-video_size','1280x720','-i',':97','-t','30','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out/(a.game+'-preview.mp4'))],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for i in range(6):
   subprocess.run(['xdotool','keydown','d'],env=env,check=False);key('z' if a.game=='spellsought' else 'space');time.sleep(2);key('x' if a.game=='spellsought' else 'j');time.sleep(2);subprocess.run(['xdotool','keyup','d'],env=env,check=False)
   if i in [1,4]:screenshot('gameplay-'+str(i)+'.png')
  cap.wait(timeout=15);screenshot('after.png');report['video']=a.game+'-preview.mp4';report['processAliveAtEnd']=proc.poll() is None;os.killpg(proc.pid,signal.SIGTERM);xvfb.terminate();report['captureCompleted']=True
 except Exception as e:report['error']=str(e);raise
 finally:(out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
