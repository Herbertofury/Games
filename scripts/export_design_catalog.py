"""Source-scoped public game discovery export for Athena; no account access or refresh."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, parse_qs

ROOT=Path(__file__).resolve().parents[1]

def freshness(value, now):
    if not value: return 'unknown'
    try:
        observed=datetime.fromisoformat(value.replace('Z','+00:00'))
        if observed.tzinfo is None: return 'unknown'
        age=(now-observed).total_seconds()
        return 'future_observation' if age<0 else 'stale' if age>=30*86400 else 'within_30_days'
    except (ValueError,TypeError): return 'unknown'

def review_scope(row):
    result=[]
    for source in row.get('sources',[]):
        if source.get('provider')!='Steam reviews API': continue
        url=source.get('url',''); p=urlsplit(url)
        if p.scheme!='https' or p.hostname!='api.steampowered.com' or p.path!='/IUserReviewsService/GetAppReviews/v1/': continue
        try:
            request=json.loads(parse_qs(p.query)['input_json'][0])
            if type(request.get('appid')) is not int or request['appid']!=row['appid']: continue
        except (ValueError,KeyError,TypeError): continue
        result.append({'url':url,'verified':source.get('verified') is True,'checkedAt':source.get('lastChecked'),'request':request})
    return result

def project(catalog, studies=None, now=None):
    if catalog.get('catalogId')!='herbertofury-games': raise ValueError('unexpected catalog')
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None: raise ValueError('as-of must include timezone')
    ids=[r['id'] for r in catalog['items']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate catalog identity')
    evidence={}
    if studies is not None:
        if studies.get('schema_version')!=1:raise ValueError('unsupported study schema')
        for row in studies['records']:
            if row['id'] in evidence:raise ValueError('duplicate study identity')
            evidence[row['id']]=row
    out=[]
    for r in catalog['items']:
        match=re.fullmatch(r'steam:([1-9][0-9]*)',r['id'])
        if not match:continue
        appid=int(match[1])
        if type(r.get('appid')) is not int or appid!=r['appid']:raise ValueError('Steam identity mismatch')
        rating=r.get('rating');count=r.get('reviewCount')
        if rating is not None and (type(rating) not in (int,float) or not 0<=rating<=100):raise ValueError('invalid percentage')
        if count is not None and (type(count) is not int or count<0):raise ValueError('invalid sample')
        if count==0:rating=None
        review={'label':r.get('reviewLabel'),'positivePercent':rating,'count':count,'observedAt':r.get('reviewsVerifiedAt'),'freshness':freshness(r.get('reviewsVerifiedAt'),now),'refreshError':r.get('reviewError'),'sources':review_scope(r)}
        review['scopeKnown']=bool(review['sources'])
        study=evidence.get(r['id'])
        out.append({'id':r['id'],'name':r['name'],'sourceUrl':f'https://store.steampowered.com/app/{appid}/','status':r.get('status'),'genres':r.get('genres',[]),'features':r.get('features',[]),'tags':r.get('tags',[]),'review':review,'image':r.get('image'),'screenshots':r.get('screenshots',[]),'trailers':r.get('trailers',[]),'editorial':{'text':r.get('curatorWhy'),'kind':'curator_interpretation','notPlayerConsensus':True},'designEvidence':None if study is None else {'sourceUrl':study['source_url'],'observedOn':study['checked_on'],'scope':study['evidence_scope'],'observations':study['observations'],'interpretation':study['design_interpretation'],'acceptance':study['acceptance'],'playtest':study['playtest']}})
    return out

def select(rows, label=None,genre=None,feature=None,min_count=0,sort='name'):
    if min_count<0:raise ValueError('minimum count must be nonnegative')
    if sort not in ('name','rating','reviews'):raise ValueError('invalid sort')
    result=[r for r in rows if (not label or (r['review']['label'] or 'unknown').casefold()==label.casefold()) and (not genre or genre.casefold() in [g.casefold() for g in r['genres']]) and (not feature or feature.casefold() in [f.casefold() for f in r['features']]) and (not min_count or r['review']['count'] is not None and r['review']['count']>=min_count)]
    if sort=='name':return sorted(result,key=lambda r:(r['name'].casefold(),r['id']))
    field='positivePercent' if sort=='rating' else 'count'
    return sorted(result,key=lambda r:(r['review'][field] is None,-(r['review'][field] or 0),r['name'].casefold(),r['id']))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=ROOT/'data/catalog.json');p.add_argument('--studies',type=Path)
    p.add_argument('--label');p.add_argument('--genre');p.add_argument('--feature');p.add_argument('--min-reviews',type=int,default=0);p.add_argument('--sort',choices=['name','rating','reviews'],default='name');p.add_argument('--as-of');p.add_argument('--output',type=Path)
    a=p.parse_args();raw=a.catalog.read_bytes();cat=json.loads(raw);now=datetime.fromisoformat(a.as_of) if a.as_of else datetime.now(timezone.utc)
    rows=project(cat,json.loads(a.studies.read_bytes()) if a.studies else None,now)
    output={'schemaVersion':1,'catalogId':cat['catalogId'],'sourceSha256':hashlib.sha256(raw).hexdigest(),'sourceGeneratedAt':cat.get('generatedAt'),'evaluatedAt':now.isoformat(),'totalSteamRecords':len(rows),'items':select(rows,a.label,a.genre,a.feature,a.min_reviews,a.sort),'limitations':['Not a Steam-wide crawl; local snapshot only.','Review ratings do not establish what players praise.','Design evidence is source-attributed, not proof of novelty or quality.']}
    text=json.dumps(output,ensure_ascii=False,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    else:print(text,end='')
if __name__=='__main__':main()
