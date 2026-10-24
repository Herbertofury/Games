#!/usr/bin/env python3
"""Finalize only reviewed party media. Unrelated carousel footage is never used."""
import datetime as dt,hashlib,json,pathlib,re,subprocess,urllib.parse,urllib.request
import discover_storefronts as net
R=pathlib.Path(__file__).resolve().parents[1];NOW=dt.datetime.now(dt.timezone.utc).isoformat()
def load(n,d):
 p=R/'data'/n;return json.loads(p.read_text()) if p.exists() else d
def save(n,d):(R/'data'/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def nk(s):return re.sub('[^a-z0-9]','',s.lower())
def main():
 out=load('party-media.json',{'overrides':{}});O=out['overrides'];proof=load('party-media-receipt.json',{'videos':{},'motion':{}});rows={g['id']:g for f in ['party-steam.json','party-extra.json','party-recovered.json','party-external.json'] for g in load(f,{'items':[]})['items']};candidates=load('party-video-candidates.json',{});refs=load('party-mode-references.json',{})
 metadata={v['id']:v for v in refs.get('videos',[]) if not v.get('error')};metadata.update({k:v for k,v in candidates.get('metadata',{}).items() if not v.get('error')})
 choices={
  'steam:238370':('CNODcpGnxVY','Magicka 2','Paradox Interactive','Official release-date trailer'),
  'steam:217200':('9LqDXVaMAH4','Worms Armageddon','Team17','Official Patch 3.8 trailer for the original PC game'),
  'steam:2179180':('te75aDNSPR0','Hex Party','SoftX','Official announcement trailer'),
  'external:mario-kart-8-deluxe':('ZKB9FEXhJ68','Mario Kart 8 Deluxe','Nintendo of America','Official overview trailer'),
  'external:smash-ultimate':('WLu7e8RZoYc','Super Smash Bros. Ultimate','Nintendo of America','Official overview trailer'),
  'external:underhanded-combat':('-Pnl_EEaX-M','Underhanded Combat',None,'Creator trailer'),
  'external:supertuxkart':('H1Lo7PlTGBk','SuperTuxKart 1.5','SuperTuxKart','Official 1.5 trailer; not the separate Evolution development footage'),
  'external:square-off-shiba':('GbEQXH6mHHI','Square Off',None,'Creator demo gameplay; historical demo footage, not a claim of the final build')
 }
 unresolved=[]
 for ident,(vid,title,author,label) in choices.items():
  try:
   url='https://www.youtube.com/watch?v='+vid;m=metadata.get(vid) or net.api('https://www.youtube.com/oembed?'+urllib.parse.urlencode({'url':url,'format':'json'}));assert nk(title) in nk(m['title']),(ident,m['title']);assert not author or author.lower()==m['author_name'].lower(),(ident,m['author_name'])
   p=O.setdefault(ident,{}).setdefault('_replace',{});p['trailers']=[{'youtube':vid,'name':label,'watchUrl':url,'sourceUrl':rows[ident]['primaryUrl'],'credit':m['author_name'],'official':True,'poster':m.get('thumbnail_url'),'verifiedAt':NOW}];proof['videos'][ident]={'youtube':vid,'metadata':m,'sourceUrl':rows[ident]['primaryUrl'],'checkedAt':NOW}
   if ident=='external:supertuxkart':p['image']=m['thumbnail_url'];p['screenshots']=[];O[ident].update(free=True,originalReleaseYear=2006,releaseLabel='Original project 2006; current 1.5 branch',requirements='Free standalone game. This entry describes the released SuperTuxKart branch, not the separate Evolution development project.')
  except Exception as error:unresolved.append({'id':ident,'video':vid,'reason':str(error)})
 for ident,row in candidates.get('nintendo',{}).items():
  if not row.get('video'):continue
  p=O.setdefault(ident,{}).setdefault('_replace',{});p['trailers']=[row['video']];p['image']=row['video'].get('poster') or rows[ident].get('image');proof['videos'][ident]=row['proof']
 # This animated gameplay loop is linked directly by the creator, not synthetic footage.
 ident='external:puff-puff-push';original='https://img.itch.zone/aW1nLzE5NzUxNTk0LmdpZg==/original/h0kLyk.gif';e=load('party-external-evidence.json',{})['records'][ident];assert original in json.dumps(e),'Creator-page motion provenance missing'
 media=R/'media/party';media.mkdir(parents=True,exist_ok=True);dest=media/'puff-puff-push-gameplay.mp4';poster=media/'puff-puff-push-preview.jpg'
 if not dest.exists():
  req=urllib.request.Request(original,headers={'User-Agent':net.UA})
  with urllib.request.urlopen(req,timeout=30) as response:raw=response.read()
  temp=media/'source.gif';temp.write_bytes(raw);info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(temp)]));frames=int(info['streams'][0].get('nb_read_frames','0'));assert frames>1,'Not an animated gameplay source'
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(temp),'-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(temp),'-frames:v','1',str(poster)],check=True);temp.unlink();proof['motion'][ident]={'sourceUrl':e['sourceUrl'],'originalAssetUrl':original,'originalSha256':hashlib.sha256(raw).hexdigest(),'videoSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'frames':frames,'checkedAt':NOW}
 O.setdefault(ident,{}).setdefault('_replace',{})['trailers']=[{'name':'Creator gameplay loop, converted from the original animation','mp4':'https://raw.githubusercontent.com/Herbertofury/Games/main/media/party/'+dest.name,'sourceUrl':e['sourceUrl'],'originalAssetUrl':original,'credit':'Typimals; original creator animation, presented as MP4','official':True,'poster':rows[ident]['image'],'editionNote':'Short gameplay loop, not a full trailer or library-recorded playthrough.'}]
 # Preserve exact paid creator storefronts as alternatives, not unrelated publisher navigation.
 for name,e in load('party-external-evidence.json',{}).get('creatorLinks',{}).items():
  if e.get('error') or name not in ['Wand Wars','Push Me Pull You']:continue
  g=next(g for g in rows.values() if g['name']==name);O.setdefault(g['id'],{}).setdefault('storefronts',[]).append({'url':e['sourceUrl'],'provider':'itch.io','kind':'store','verified':True,'sourceUrl':e['sourceUrl'],'lastChecked':NOW})
 proof.update(checkedAt=NOW,unresolved=unresolved);out['generatedAt']=NOW;save('party-media.json',out);save('party-media-receipt.json',proof);print(json.dumps({'mediaOverrides':len(O),'unresolved':unresolved},indent=2))
if __name__=='__main__':main()
