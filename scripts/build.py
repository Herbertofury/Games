#!/usr/bin/env python3
"""Build a portable catalog, matching wiki, provenance manifest, and release archive."""
import argparse,csv,datetime as dt,hashlib,html,json,pathlib,re,shutil,zipfile
from catalog_model import assemble,score,validate
from wiki_builder import build_wiki
from platformer_study import build_platformer_wiki
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO='https://github.com/Herbertofury/Games'
SITE='https://herbertofury.github.io/Games/'
def slug(s): return re.sub(r'[^A-Za-z0-9]+','-',s).strip('-')
def md(s): return str(s or '').replace('|','\\|').replace('\n',' ').replace('<','&lt;').replace('>','&gt;')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='data/catalog.json');args=ap.parse_args()
    path=ROOT/args.data;catalog=assemble(json.loads(path.read_text()));path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');games=catalog['items'];assert games,'Empty catalogs cannot be published'
    assert len({g['id'] for g in games})==len(games),'Duplicate IDs'
    for g in games:validate(g)
    out=ROOT/'dist';out.mkdir(exist_ok=True);wiki=ROOT/'wiki';wiki.mkdir(exist_ok=True);assets=out/'assets';assets.mkdir(exist_ok=True)
    def source(name):return (ROOT/'site'/name).read_text()
    data=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    app=(source('app.js')+'\n'+source('platformers.js')+'\n'+source('survival.js')+'\n'+source('party.js')+'\n'+source('lounge.js')+'\n'+source('arcade.js')).replace('</script','<\\/script')
    page=source('index.html').replace('/*__CSS__*/',source('styles.css')+'\n'+source('platformers.css')+'\n'+source('survival.css')+'\n'+source('party.css')+'\n'+source('lounge.css')).replace('/*__DATA__*/','window.GAMES_CATALOG='+data+';').replace('/*__APP__*/',app)
    assert not any(x in page for x in ['/*__CSS__*/','/*__DATA__*/','/*__APP__*/'])
    (out/'index.html').write_text(page);(out/'.nojekyll').write_text('');shutil.copyfile(ROOT/'site/sw.js',out/'sw.js');shutil.copyfile(path,out/'catalog.json')
    verified=[g for g in games if g.get('verification')=='verified'];unresolved=[g for g in games if g.get('verification')!='verified'];collections=sorted({g['collection'] for g in games})
    trailer_count=sum(any(t.get('mp4') or t.get('webm') or t.get('hls') or t.get('youtube') or t.get('vimeo') for t in g.get('trailers',[])) for g in games)
    build_wiki(ROOT,catalog)
    from metroidvania_wiki import build as build_metroidvania_wiki
    build_metroidvania_wiki(ROOT,catalog)
    build_platformer_wiki(ROOT,catalog)
    from survival_wiki import build as build_survival_wiki
    build_survival_wiki(ROOT,catalog)
    from party_wiki import build as build_party_wiki
    build_party_wiki(ROOT,catalog)
    from lounge_wiki import build as build_lounge_wiki
    build_lounge_wiki(ROOT,catalog)
    manifest={'schemaVersion':1,'version':'2.0.0','builtAt':dt.datetime.now(dt.timezone.utc).isoformat(),'sourceRepository':REPO,'sourceRevision':__import__('os').environ.get('GITHUB_SHA'),'sourceWiki':REPO+'/wiki','datasetHash':catalog.get('build',{}).get('datasetHash'),'records':len(games),'verified':len(verified),'unresolved':len(unresolved),'trailers':trailer_count,'collections':collections,'hubs':catalog['build']['hubCounts'],'platforms':sorted({x['provider'] for g in games for x in g.get('storefronts',[])}),'html':{'bytes':(out/'index.html').stat().st_size,'sha256':digest(out/'index.html')},'sourceFiles':{str(p.relative_to(ROOT)):digest(p) for d in ['site','scripts','tests','data'] for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.png','.jpg']}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    release=ROOT/'release';release.mkdir(exist_ok=True);shutil.copyfile(out/'index.html',release/'Games - Explorer.html')
    with zipfile.ZipFile(release/'Games - Library.zip','w',zipfile.ZIP_DEFLATED,9) as z:
        for folder in ['site','scripts','data','wiki','dist','docs','tests','media','.github']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.png','.jpg']:z.write(p,str(p.relative_to(ROOT)))
        for name in ['README.md','LICENSE','requirements-dev.txt']:
            if (ROOT/name).exists():z.write(ROOT/name,name)
    (release/'SHA256SUMS.txt').write_text('\n'.join(f'{digest(p)}  {p.name}  {p.stat().st_size} bytes' for p in release.iterdir() if p.name!='SHA256SUMS.txt')+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='sourceFiles'},indent=2))
if __name__=='__main__':main()
