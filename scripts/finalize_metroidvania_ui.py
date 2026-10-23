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
patch('scripts/metroidvania_model.py',"['metroidvania-storefronts.json','metroidvania-curation.json','metroidvania-media.json']","['metroidvania-storefronts.json','metroidvania-curation.json','metroidvania-media.json','metroidvania-review-decisions.json']")
patch('scripts/metroidvania_model.py',"'dispositions':rec.get('dispositions',[])","'dispositions':rec.get('dispositions',[])+read(root,'metroidvania-review-decisions.json',{}).get('dispositions',[])")
patch('scripts/metroidvania_qa.py',"for hub,n in [('Roguelites',170),('Boomer shooters',150),('Real-time strategy',130),('Metroidvanias',N)]:","for hub,n in list(json.loads((R/'data/metroidvania-protected.json').read_text())['hubCounts'].items())+[('Metroidvanias',N)]:")
# Actual source collection counts and protected identities replace stale fixed totals.
# All original browser, shooter, RTS and platformer suites still run at publication.
print('Source-aware players, current-genre protection and reviewed discovery boundaries installed.')
