"""Synthetic data for UI tests only. Never publish as the canonical catalog."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
items=[]
collections=['Dark fantasy','Myth & magic','Sci-fi & machines','Action roguelites','Loot-driven ARPGs','Offbeat hybrids']
for i in range(171):
    aid=2218750 if i==0 else 9000000+i;name='Halls of Torment' if i==0 else ('Test Dark Fantasy '+str(i) if i%6==0 else 'Fixture Game '+str(i))
    g={'id':'steam:'+str(aid),'appid':aid,'seedId':str(aid),'name':name,'seedName':name,'collection':collections[i%6],'fit':10-i%5,'summary':'SYNTHETIC TEST FIXTURE ONLY. Survive the horde, build surprising combinations, and fight your way through the dungeon.','developers':['Fixture Developer'],'genres':['Action','RPG'],'tags':[collections[i%6],'Loot','Boss fights']+(['Co-op'] if i%3==0 else []),'status':'Early Access' if i%7==0 else 'Released','releaseDate':str(2022+i%5)+'-05-10','releaseLabel':'May 10, '+str(2022+i%5),'comingSoon':False,'free':i%9==0,'price':'$6.99','priceMinor':699,'rating':96-i%20,'reviewCount':1000+i*30,'verification':'verified','verifiedAt':'2026-10-22T12:00:00+00:00','steamUrl':f'https://store.steampowered.com/app/{aid}/','image':'http://127.0.0.1:8765/fixture.svg','screenshots':[{'src':'http://127.0.0.1:8765/fixture.svg','thumbnail':'http://127.0.0.1:8765/fixture.svg'}],'trailers':[{'name':'Fixture trailer','mp4':'http://127.0.0.1:8765/fixture.mp4','poster':'http://127.0.0.1:8765/fixture.svg'}],'sources':[{'url':'https://store.steampowered.com/app/'+str(aid)+'/'}],'warnings':[]}
    if i==170:g.update(id='pending:'+str(aid),verification='unresolved',fit=None,rating=None,reviewCount=0,status='Needs verification',image=None,trailers=[],screenshots=[],releaseDate=None,releaseLabel='Unverified')
    items.append(g)
d={'schemaVersion':1,'isTestFixture':True,'title':'Games - Synthetic QA Fixture','generatedAt':'2026-10-22T12:00:00+00:00','sourceRepository':'https://github.com/Herbertofury/Games','sources':[],'build':{'datasetHash':'SYNTHETIC-TEST-FIXTURE','inputCount':len(items),'verifiedCount':170,'unresolvedCount':1},'items':items}
(ROOT/'tests/fixture.json').write_text(json.dumps(d))
