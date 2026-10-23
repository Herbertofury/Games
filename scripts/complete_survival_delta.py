"""Complete only new source rows added after the broad verification checkpoint."""
import concurrent.futures,datetime as dt,json,pathlib
import collect_survival_sources as collector
R=pathlib.Path(__file__).resolve().parents[1]
def load(name):return json.loads((R/'data'/name).read_text())
def save(name,value):(R/'data'/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
steam=load('survival-steam.json')['items'];stores=load('survival-storefronts.json');missing=[g for g in steam if g['id'] not in stores['overrides']]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for ident,row in pool.map(lambda g:collector.stores(g,None,True),missing):stores['overrides'][ident]=row
save('survival-storefronts.json',stores)
curation=load('survival-curation.json');curation['overrides'].setdefault('steam:2893820',{}).update(genreScope='Open-world action RPG / survival-adjacent',recommendationCaution='An open-world action RPG with professions and survival themes, not a Conan-style base-building or settlement simulator.')
save('survival-curation.json',curation)
# The free CDDA distribution is explicitly linked by its Steam developer website.
# Verify it once rather than inferring a download path from the project name.
media=load('survival-media.json');ident='steam:2330750';g=next(g for g in steam if g['id']==ident)
try:
 page=collector.page(g['website']);assert 'cataclysm' in page['title'].lower()
 row={'provider':'Official site','url':page['sourceUrl'],'kind':'project','verified':True,'lastChecked':dt.datetime.now(dt.timezone.utc).isoformat(),'sourceUrl':g['steamUrl'],'editionNote':'Official free open-source project; the paid Steam distribution is a distinct edition.'}
 rows=media['overrides'].setdefault(ident,{}).setdefault('storefronts',[])
 if not any(x['url'].rstrip('/')==row['url'].rstrip('/') for x in rows):rows.append(row)
 media['overrides'][ident].setdefault('sources',[]).append(dict(row,kind='source'))
 print('CDDA official project confirmed:',page['title'])
except Exception as e:
 media['overrides'].setdefault(ident,{})['freeProjectCheckError']=str(e)
 print('CDDA free-project link remains unresolved:',str(e))
save('survival-media.json',media)
print(json.dumps({'newStoreChecks':len(missing),'totalStoreChecks':len(stores['overrides']),'specificRpgNeighborLabelled':True},indent=2))
