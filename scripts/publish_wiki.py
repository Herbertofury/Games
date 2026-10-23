#!/usr/bin/env python3
"""Publish generated pages to the real wiki without deleting unrelated pages."""
import base64,hashlib,json,os,pathlib,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];repo=os.environ.get('GITHUB_REPOSITORY','Herbertofury/Games');token=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN');report={'repository':repo,'wikiUrl':'https://github.com/'+repo+'/wiki','state':'unresolved-active'}
def run(args,cwd=None):return subprocess.run(args,cwd=cwd,text=True,capture_output=True)
def save():
    p=ROOT/'qa';p.mkdir(exist_ok=True);(p/'wiki-publication.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if not token:
    report['blocker']='Authenticated GitHub token missing';save();raise SystemExit(0)
header='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode();git=['git','-c','http.https://github.com/.extraheader='+header]
target=ROOT/'.wiki-publish'
if target.exists():shutil.rmtree(target)
r=run(git+['clone','--depth','1','https://github.com/'+repo+'.wiki.git',str(target)])
if r.returncode:
    report['blocker']='The native wiki repository could not be cloned. Create its first Home page in GitHub, then rerun Publish library.';report['detail']=r.stderr.replace(token,'[redacted]').replace(header,'[redacted]');save();raise SystemExit(0)
branch=run(['git','branch','--show-current'],target).stdout.strip() or 'master'
for p in (ROOT/'wiki').glob('*.md'):shutil.copyfile(p,target/p.name)
run(['git','config','user.name','Games catalog bot'],target);run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],target);run(['git','add','--','*.md'],target)
r=run(['git','diff','--cached','--quiet'],target)
if r.returncode:
    c=run(['git','commit','-m','Synchronize the living roguelite collection'],target)
    if c.returncode:report['blocker']='Wiki commit failed';report['detail']=c.stderr;save();raise SystemExit(1)
    r=run(git+['push','origin','HEAD:'+branch],target)
    if r.returncode:report['blocker']='Wiki push failed';report['detail']=r.stderr.replace(token,'[redacted]').replace(header,'[redacted]');save();raise SystemExit(0)
local=run(['git','rev-parse','HEAD'],target).stdout.strip();remote=run(git+['ls-remote','origin','refs/heads/'+branch],target).stdout.split()
if not remote or remote[0]!=local:report['blocker']='Wiki remote readback did not match';save();raise SystemExit(1)
report.update(state='verified',commit=local,branch=branch,pages=len(list((ROOT/'wiki').glob('*.md'))),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'wiki').glob('*.md')});save()
