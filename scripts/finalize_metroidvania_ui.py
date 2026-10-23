"""Small assertion-guarded media/UI additions after the exploration hub install."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def patch(name,old,new):
 p=R/name;s=p.read_text()
 if new in s:return
 assert old in s,(name,'source anchor changed')
 p.write_text(s.replace(old,new,1))
patch('site/app.js','t.mp4||t.webm||t.hls||t.dash||t.youtube','t.mp4||t.webm||t.hls||t.dash||t.youtube||t.vimeo')
patch('site/app.js',"  if(a.youtube){",'''  if(a.vimeo){$('.media-stage').innerHTML=`<div class="youtube-consent">${img(a.poster||g.image,g.name+' video preview')}<button class="primary" data-vimeo="${esc(a.vimeo)}">${icon('play')}Play credited creator footage</button><p>Loads Vimeo on click. <a href="https://vimeo.com/${esc(a.vimeo)}" target="_blank" rel="noopener">Open video separately</a></p></div>`;return;}
  if(a.youtube){''')
p=R/'site/app.js';s=p.read_text()
if "e.target.closest('[data-vimeo]')" not in s:
 s+='''
document.addEventListener('click',e=>{const v=e.target.closest('[data-vimeo]');if(!v||!/^\\d+$/.test(v.dataset.vimeo))return;const f=document.createElement('iframe');f.src='https://player.vimeo.com/video/'+v.dataset.vimeo+'?autoplay=1&dnt=1';f.title=(currentGame?.name||'Game')+' credited video';f.allow='autoplay; fullscreen; picture-in-picture';f.referrerPolicy='strict-origin-when-cross-origin';f.allowFullscreen=true;f.className='trailer-frame';v.closest('.media-stage').replaceChildren(f);});
''';p.write_text(s)
patch('tests/test_metroidvania.py',"['hls','mp4','webm','youtube']","['hls','mp4','webm','youtube','vimeo']")
# The final artifact can include full-source game preview MP4s without external scripts.
# No old test is deleted: the original browser, shooter, RTS and media suites still run.
print('Vimeo opt-in player and all-media acceptance installed.')
