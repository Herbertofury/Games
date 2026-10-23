"""Authentic public-build preview recovery; recordings require visual approval.
Uses creator-supplied assets unchanged. A native Godot runtime is selected from
the PCK's engine version instead of retrying the failed Wine environment.
"""
import argparse,hashlib,json,os,pathlib,re,shutil,signal,struct,subprocess,tarfile,time,urllib.request,zipfile
from playwright.sync_api import sync_playwright
R=pathlib.Path(__file__).resolve().parents[1]
CFG={
 'spellsought':{'url':'https://speedrockstrong.itch.io/spellsought','upload':'19262155','title':'Spellsought 1.0.3'},
 'reawakening':{'url':'https://hatbird-games.itch.io/reawakening','purchase':'https://hatbird-games.itch.io/reawakening/purchase','title':'Reawakening public Linux release'},
 'mongrel-story':{'url':'https://mountainstork.itch.io/mongrel-story-demo','upload':'14164878','title':'Mongrel Story 0.8.0 public Linux demo'}
}
def download(url,dest):
 req=urllib.request.Request(url,headers={'User-Agent':'GamesLibrary-public-build-preview'})
 with urllib.request.urlopen(req,timeout=60) as r,dest.open('wb') as f:shutil.copyfileobj(r,f)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('game',choices=CFG);a=ap.parse_args();c=CFG[a.game];out=R/'qa'/('native-'+a.game);out.mkdir(parents=True,exist_ok=True);work=pathlib.Path('/tmp/mv-native')/a.game;work.mkdir(parents=True,exist_ok=True)
 report={'id':'external:'+a.game,'sourceUrl':c['url'],'build':c['title'],'type':'Catalog-recorded public build preview','approved':False};processes=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox']);ctx=b.new_context(accept_downloads=True);p=ctx.new_page();p.goto(c.get('purchase',c['url']),wait_until='domcontentloaded',timeout=45000)
   if c.get('upload'):
    with p.expect_download(timeout=60000) as dl:p.locator('[data-upload_id="'+c['upload']+'"]').click()
   else:
    p.get_by_text('No thanks, just take me to the downloads',exact=False).click();p.wait_for_selector('.download_btn');uploads=p.locator('.upload');chosen=None
    for i in range(uploads.count()):
     u=uploads.nth(i)
     if 'linux' in u.inner_text().lower() or u.locator('.icon-tux').count():chosen=u;break
    if chosen is None:raise RuntimeError('No public Linux build exposed by the creator')
    with p.expect_download(timeout=60000) as dl:chosen.locator('.download_btn').click()
   d=dl.value;dest=work/d.suggested_filename;d.save_as(str(dest));report.update(filename=dest.name,bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest());p.screenshot(path=str(out/'source.png'));b.close()
  game=work/'game';game.mkdir(exist_ok=True)
  if zipfile.is_zipfile(dest):
   with zipfile.ZipFile(dest) as z:
    assert all(not pathlib.PurePosixPath(n).is_absolute() and '..' not in pathlib.PurePosixPath(n).parts for n in z.namelist());z.extractall(game)
  elif tarfile.is_tarfile(dest):
   with tarfile.open(dest) as t:t.extractall(game,filter='data')
  else:raise RuntimeError('Unexpected public archive type')
  env=dict(os.environ,DISPLAY=':97',LIBGL_ALWAYS_SOFTWARE='1',MESA_GL_VERSION_OVERRIDE='4.5',SDL_AUDIODRIVER='dummy',HOME=str(work/'home'))
  pathlib.Path(env['HOME']).mkdir(exist_ok=True);xvfb=subprocess.Popen(['Xvfb',':97','-screen','0','1280x720x24','-nolisten','tcp']);processes.append(xvfb);time.sleep(1);wm=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);processes.append(wm)
  if a.game=='spellsought':
   packs=list(game.rglob('*.pck'));assert len(packs)==1;pack=packs[0]
   with pack.open('rb') as f:magic,fmt,major,minor,patch=struct.unpack('<5I',f.read(20))
   assert magic==0x43504447;version=f'{major}.{minor}'+(f'.{patch}' if patch else '');tag=version+'-stable';url=f'https://github.com/godotengine/godot-builds/releases/download/{tag}/Godot_v{tag}_linux.x86_64.zip';enginezip=work/'godot.zip';download(url,enginezip)
   with zipfile.ZipFile(enginezip) as z:z.extractall(work/'engine')
   exe=next(p for p in (work/'engine').iterdir() if p.is_file());exe.chmod(0o755);cmd=[str(exe),'--main-pack',str(pack),'--path',str(pack.parent),'--rendering-method','gl_compatibility','--rendering-driver','opengl3','--resolution','1280x720','--position','0,0','--audio-driver','Dummy'];cwd=pack.parent
   report['runtime']={'version':version,'sourceUrl':url,'sha256':hashlib.sha256(enginezip.read_bytes()).hexdigest(),'packSha256':hashlib.sha256(pack.read_bytes()).hexdigest()}
  else:
   exes=[]
   for p in game.rglob('*'):
    if not p.is_file() or p.suffix in ['.so','.pck']:continue
    with p.open('rb') as f:head=f.read(4)
    if head==b'\x7fELF' and not any(x in p.name.lower() for x in ['crash','unityplayer']):exes.append(p)
   assert len(exes)==1,exes;exe=exes[0];exe.chmod(0o755);cwd=exe.parent
   if a.game=='mongrel-story':cmd=[str(exe),'-force-glcore','-screen-width','1280','-screen-height','720','-screen-fullscreen','0','-logFile',str(out/'unity-player.log')]
   else:cmd=[str(exe),'--rendering-method','gl_compatibility','--rendering-driver','opengl3','--resolution','1280x720','--position','0,0','--audio-driver','Dummy']
  log=(out/'process.log').open('w');proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);processes.append(proc);report['command']=cmd
  def shot(name):subprocess.run(['ffmpeg','-y','-loglevel','error','-f','x11grab','-video_size','1280x720','-i',':97','-frames:v','1',str(out/name)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  def focus():
   found=subprocess.run(['xdotool','search','--onlyvisible','--pid',str(proc.pid)],env=env,capture_output=True,text=True)
   if found.returncode==0:
    window=found.stdout.splitlines()[-1];subprocess.run(['xdotool','windowactivate','--sync',window],env=env,check=False);subprocess.run(['xdotool','windowfocus','--sync',window],env=env,check=False);return window
  def key(k):focus();subprocess.run(['xdotool','key','--clearmodifiers',k],env=env,check=False)
  time.sleep(25 if a.game=='mongrel-story' else 8)
  if proc.poll() is not None:raise RuntimeError('Build exited before capture; inspect native log')
  report['window']=focus();shot('menu.png')
  if a.game=='mongrel-story':
   # Unity's menu accepts keyboard; pointer focus is established before starting.
   key('Return');time.sleep(6);shot('menu-after-enter.png');key('space');time.sleep(5)
  else:key('Return');time.sleep(2);key('z');time.sleep(2);key('Return');time.sleep(2)
  shot('start.png')
  cap=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','x11grab','-framerate','30','-video_size','1280x720','-i',':97','-t','32','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(out/(a.game+'-preview.mp4'))],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  focus()
  for i in range(7):
   direction='Right' if i<4 else 'Left';subprocess.run(['xdotool','keydown',direction],env=env,check=False);key('z' if a.game=='spellsought' else 'space');time.sleep(1.5);key('x' if a.game=='spellsought' else 'j');time.sleep(2.5);subprocess.run(['xdotool','keyup',direction],env=env,check=False)
   if i in [0,3,6]:shot('frame-'+str(i)+'.png')
  cap.wait(timeout=10);shot('end.png');report.update(captureCompleted=True,video=a.game+'-preview.mp4',reviewClaim='Short recorded preview only; screenshots must be visually approved before publication.')
 except Exception as e:report['error']=str(e);raise
 finally:
  for p in reversed(processes):
   if p.poll() is None:p.terminate()
  (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
