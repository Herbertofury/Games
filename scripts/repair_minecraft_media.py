"""Replace one blocked image-host route with the same game's official store gallery.
The exact product ID is anchored by the public Xbox PC-edition listing. No
placeholder, thumbnail downgrade, removed game, or skipped media assertion.
"""
import hashlib,json,os,pathlib,shutil,urllib.parse,urllib.request
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
PRODUCT='9NXP44L49SHJ'
STORE='https://www.xbox.com/en-US/games/store/minecraft-java-bedrock-edition-for-pc/'+PRODUCT
API='https://displaycatalog.mp.microsoft.com/v7.0/products?bigIds='+PRODUCT+'&market=US&languages=en-us'
def main():
 req=urllib.request.Request(API,headers={'User-Agent':'GamesCatalog/1.5 (+https://github.com/Herbertofury/Games)','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as response:raw=response.read();data=json.loads(raw)
 products=data.get('Products',[]);p=next((p for p in products if p.get('ProductId')==PRODUCT),None)
 assert p,'Exact official Microsoft product ID not returned; no catalog write'
 localized=next((x for x in p.get('LocalizedProperties',[]) if x.get('Language','').lower()=='en-us'),p.get('LocalizedProperties',[{}])[0])
 title=localized.get('ProductTitle','');assert 'Minecraft: Java & Bedrock Edition for PC'.lower() in title.lower(),title
 gallery=[]
 for image in localized.get('Images',[]):
  if image.get('ImagePurpose')!='Screenshot':continue
  u=image.get('Uri','');u='https:'+u if u.startswith('//') else u
  host=urllib.parse.urlsplit(u).hostname or ''
  assert urllib.parse.urlsplit(u).scheme=='https' and host in ['store-images.s-microsoft.com','store-images.microsoft.com'],u
  if not any(s['src']==u for s in gallery):gallery.append({'src':u,'thumbnail':u,'sourceUrl':STORE,'credit':'Mojang / Microsoft official PC-edition gallery','alt':image.get('Caption') or title+' official screenshot','verified':True,'width':image.get('Width'),'height':image.get('Height')})
 assert len(gallery)>=3,'Official replacement gallery must retain at least the original three images'
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('google-chrome') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page()
  page.set_content('<!doctype html><title>Minecraft official gallery validation</title>')
  proof=page.evaluate('''async urls=>{const out=[];for(const url of urls){out.push(await new Promise(resolve=>{const im=new Image();const timer=setTimeout(()=>resolve({url,ok:false,error:'timeout'}),25000);im.onload=()=>{clearTimeout(timer);resolve({url,ok:im.naturalWidth>=1000,width:im.naturalWidth,height:im.naturalHeight})};im.onerror=()=>{clearTimeout(timer);resolve({url,ok:false,error:'network/decode'})};im.src=url;}))}return out;}''',[s['src'] for s in gallery]);browser.close()
 assert all(x['ok'] for x in proof),proof
 file=ROOT/'data/survival-media.json';d=json.loads(file.read_text());entry=d['overrides']['external:minecraft'];replace=entry.setdefault('_replace',{})
 old={'image':replace.get('image'),'screenshots':replace.get('screenshots',[])}
 replace['image']=gallery[0]['src'];replace['screenshots']=gallery
 source={'url':STORE,'provider':'Xbox','kind':'store','verified':True,'sourceUrl':STORE,'evidence':'Exact PC Java & Bedrock bundle product '+PRODUCT+'; official Microsoft product gallery validated in Chrome.'}
 for field in ['sources','storefronts']:
  entry[field]=list({s['url']:s for s in entry.get(field,[])+[source]}.values())
 report={'productId':PRODUCT,'title':title,'sourceUrl':STORE,'metadataUrl':API,'metadataSha256':hashlib.sha256(raw).hexdigest(),'priorMedia':old,'gallery':gallery,'browserDecoded':proof,'passed':True,'scope':'Only Minecraft media and one additional exact official store source changed. The original game identity, trailer, reviews and all other catalog entries are preserved.'}
 (ROOT/'data/minecraft-media-repair.json').write_text(json.dumps(report,indent=2)+'\n')
 file.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
