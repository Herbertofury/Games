"""Reconcile exact cross-genre media and keep all source-union tests exhaustive."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def patch(name,old,new):
 p=R/name;s=p.read_text()
 if new in s:return
 assert old in s,(name,'source anchor changed');p.write_text(s.replace(old,new,1))
patch('scripts/metroidvania_model.py',"   for aid in g.get('demoAppids',[]):", "   playable=lambda t:any(t.get(k) for k in ['mp4','webm','hls','dash','youtube','vimeo'])\n   g['unavailableVideos']=[t for t in g.get('trailers',[]) if not playable(t)]\n   g['trailers']=[t for t in g.get('trailers',[]) if playable(t)]\n   for aid in g.get('demoAppids',[]):")
patch('scripts/metroidvania_model.py',"   else:games[ident]=g", "    for field in ['sources','storefronts']:\n     old[field]=list({x['url'].rstrip('/'):x for x in old.get(field,[])+g.get(field,[])}.values())\n    media_key=lambda t:t.get('youtube') or t.get('vimeo') or t.get('hls') or t.get('mp4') or t.get('webm') or t.get('dash') or t.get('id') or t.get('sourceUrl')\n    old['unavailableVideos']=list({str(media_key(t)):t for t in old.get('unavailableVideos',[])+g.get('unavailableVideos',[])+[t for t in old.get('trailers',[]) if not playable(t)]}.values())\n    old['trailers']=list({media_key(t):t for t in old.get('trailers',[])+g.get('trailers',[]) if playable(t)}.values())\n   else:games[ident]=g")
patch('tests/test_platformers.py',"  self.assertEqual(expected,set(self.by));", "  held={i for i,x in json.loads((R/'data/metroidvania-review-decisions.json').read_text()).get('overrides',{}).items() if x.get('excludeFromPublication')}\n  for file in ['metroidvania-steam.json','metroidvania-external.json']:\n   expected.update(g['id'] for g in json.loads((R/'data'/file).read_text())['items'] if g['id'] not in held)\n  self.assertEqual(expected,set(self.by));")
patch('tests/test_metroidvania.py', "self.assertTrue(any(t.get(k) for k in ['hls','mp4','webm','youtube','vimeo']))", "self.assertTrue(any(t.get(k) for k in ['hls','mp4','webm','dash','youtube','vimeo']))")
# Decode malformed HTML-tracking query keys without dropping functional store parameters.
p=R/'scripts/metroidvania_model.py';s=p.read_text()
if 'def clean_distribution_url(' not in s:
 s=s.replace('import copy,json,re','import copy,json,re,html,urllib.parse',1)
 marker="def integrate(root,games):"
 helper="""def clean_distribution_url(url):
 p=urllib.parse.urlsplit(html.unescape(url));query=[]
 for k,v in urllib.parse.parse_qsl(p.query):
  k=k.lstrip(';')
  while k.startswith('amp;'):k=k[4:].lstrip(';')
  if k.lower().startswith(('utm_','hmb_')) or k in ['_xm','ref','referrer','snr']:continue
  query.append((k,v))
 return urllib.parse.urlunsplit((p.scheme,p.netloc,p.path,urllib.parse.urlencode(query),p.fragment))

"""
 assert marker in s;s=s.replace(marker,helper+marker,1)
 s=s.replace("   published.append(ident)","   target=games[ident]\n   target['storefronts']=list({clean_distribution_url(x['url']).rstrip('/'):dict(x,url=clean_distribution_url(x['url'])) for x in target.get('storefronts',[])}.values())\n   published.append(ident)",1)
 p.write_text(s)
print('Cross-genre official media, clean exact links and complete canonical source union reconciled.')
