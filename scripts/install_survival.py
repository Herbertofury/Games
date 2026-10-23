"""Assertion-guarded installation of the survival extension; no data reset."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]
def patch(file,old,new):
 p=R/file;s=p.read_text()
 if new in s:return
 assert old in s,(file,'source anchor changed')
 p.write_text(s.replace(old,new,1))
protected=R/'data/survival-protected.json'
if not protected.exists():
 d=json.loads((R/'data/catalog.json').read_text());protected.write_text(json.dumps({'ids':[g['id'] for g in d['items']],'hubCounts':d['build']['hubCounts'],'datasetHash':d['build']['datasetHash']},indent=2)+'\n')
patch('scripts/catalog_model.py',"    mv=integrate(ROOT,games)","    mv=integrate(ROOT,games)\n    from survival_model import integrate as integrate_survival\n    survival=integrate_survival(ROOT,games)")
patch('scripts/catalog_model.py',"    c['generatedAt']=max(dates) if dates else None","    if survival.get('generatedAt'):dates.append(survival['generatedAt'])\n    c['generatedAt']=max(dates) if dates else None")
patch('scripts/catalog_model.py',"    b['metroidvaniaCount']=len(mv['ids'])","    b['metroidvaniaCount']=len(mv['ids'])\n    b['generator']='games-catalog/1.5.0'\n    b['candidateUnresolved']+=survival['unresolved']\n    b['candidateDispositions']+=survival['dispositions']\n    b['survivalStudyCount']=len(survival['ids'])")
patch('scripts/build.py',"source('app.js')+'\\n'+source('platformers.js')","source('app.js')+'\\n'+source('platformers.js')+'\\n'+source('survival.js')")
patch('scripts/build.py',"source('styles.css')+'\\n'+source('platformers.css')","source('styles.css')+'\\n'+source('platformers.css')+'\\n'+source('survival.css')")
patch('scripts/build.py',"    build_platformer_wiki(ROOT,catalog)","    build_platformer_wiki(ROOT,catalog)\n    from survival_wiki import build as build_survival_wiki\n    build_survival_wiki(ROOT,catalog)")
patch('scripts/build.py',"'version':'1.4.0'","'version':'1.5.0'")
patch('site/app.js','g.summary,g.curatorWhy,g.metroidvaniaWhy','g.summary,g.curatorWhy,g.survivalWhy,g.survivalInfo?.world,g.survivalInfo?.hosting,g.survivalInfo?.modding,g.metroidvaniaWhy')
patch('site/app.js','[g.genreScope,g.metroidvaniaInfo?.structure]','[g.genreScope,g.metroidvaniaInfo?.structure,g.survivalScope]')
patch('site/app.js',"x.kind==='project'?'Project page':'Store'","x.kind==='project'?'Project page':x.kind==='archive'?'Archived listing':x.kind==='subscription'?'Membership access':x.kind==='engine'?'Required engine':x.kind==='source'?'Source project':x.kind==='media'?'Media source':x.kind==='news'?'Developer update':'Store'")
# Source-kind labels are meaningful in the native wiki too, not just tooltips.
patch('scripts/wiki_builder.py',"in ['demo','project']","in ['demo','project','archive','subscription','prototype','download','browser','bundle']")
p=R/'site/survival.css'
p.write_text('''/* Survival and voxel homes: source artwork, not synthetic illustrations. */
body[data-hub="survival"]{--accent:#a8dec4;--accent-strong:#d3f3e5;--accent-dim:rgba(168,222,196,.13);--accent-soft:rgba(168,222,196,.08)}
body[data-hub="voxel"]{--accent:#efcf8b;--accent-strong:#ffe6b7;--accent-dim:rgba(239,207,139,.13);--accent-soft:rgba(239,207,139,.08)}
body[data-hub="survival"] .intro h1,body[data-hub="voxel"] .intro h1{font-size:clamp(30px,3.7vw,56px);letter-spacing:-.05em;max-width:1000px}
body[data-hub="survival"] .featured{background:#101f1a;border-color:rgba(168,222,196,.24)}
body[data-hub="voxel"] .featured{background:#211d13;border-color:rgba(239,207,139,.27)}
body[data-hub="survival"] .feature-noise{background:linear-gradient(90deg,rgba(10,24,19,.98),rgba(10,24,19,.74) 45%,rgba(10,24,19,.1))}
body[data-hub="voxel"] .feature-noise{background:linear-gradient(90deg,rgba(27,23,14,.98),rgba(27,23,14,.76) 45%,rgba(27,23,14,.12))}
body[data-hub="survival"] .feature-art,body[data-hub="voxel"] .feature-art{opacity:.9;filter:saturate(.95)}
body[data-hub="survival"] .feature-content,body[data-hub="voxel"] .feature-content{max-width:660px}
.survival-guide{margin:27px 0 22px;padding:25px;border:1px solid var(--border);border-radius:15px;background:linear-gradient(115deg,var(--accent-soft),transparent 80%);position:relative;overflow:hidden}
.survival-guide[hidden],.voxel-route[hidden]{display:none!important}
.survival-guide-heading{display:flex;justify-content:space-between;align-items:center;gap:24px}.survival-guide .eyebrow{color:var(--accent);font-size:9px;font-weight:800;letter-spacing:.18em}.survival-guide h2{font-size:21px;letter-spacing:-.035em;margin:9px 0}.survival-guide p{font-size:11px;color:var(--muted);line-height:1.7;max-width:650px}.survival-guide-heading>a{white-space:nowrap;font-size:10px;color:var(--accent)}
.survival-guide nav{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0 12px}.survival-guide nav button{border:1px solid var(--border);border-radius:8px;padding:10px 13px;font:inherit;font-size:10px;background:var(--surface);color:var(--text);cursor:pointer;transition:border-color .15s,background .15s}.survival-guide nav button:hover,.survival-guide nav button:focus-visible{border-color:var(--accent);background:var(--accent-dim)}
.survival-boundary{font-size:10px!important;line-height:1.75!important;color:var(--muted);max-width:880px!important}.survival-brief{padding:23px;background:var(--accent-soft);border:1px solid var(--border);border-radius:13px}.survival-brief>.eyebrow{font-size:10px;color:var(--accent);font-weight:800;letter-spacing:.16em}.survival-brief h3{margin-top:10px}.survival-brief>p{font-size:12px;line-height:1.8;color:var(--muted)}.survival-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px 26px;margin:22px 0}.survival-facts small{display:block;color:var(--muted);letter-spacing:.12em;font-size:9px;margin-bottom:8px}.survival-facts strong{display:block;font-size:12px;line-height:1.7;font-weight:600}.survival-brief>a{font-size:11px;color:var(--accent)}
body.light[data-hub="survival"]{--accent:#276b50;--accent-strong:#174c39;--accent-dim:rgba(39,107,80,.1);--accent-soft:rgba(39,107,80,.055)}body.light[data-hub="voxel"]{--accent:#846122;--accent-strong:#604512;--accent-dim:rgba(132,97,34,.1);--accent-soft:rgba(132,97,34,.055)}body.light[data-hub="survival"] .featured{--accent:#a8dec4;color:#ecfff5}body.light[data-hub="voxel"] .featured{--accent:#efcf8b;color:#fff6e5}
@media(max-width:700px){.survival-guide{padding:18px;margin-top:19px}.survival-guide-heading{display:block}.survival-guide-heading>a{display:inline-block;margin-top:8px}.survival-guide h2{font-size:19px}.survival-guide nav{gap:6px}.survival-guide nav button{padding:11px 10px}.survival-facts{grid-template-columns:1fr}.survival-brief{padding:18px}body[data-hub="survival"] .intro h1,body[data-hub="voxel"] .intro h1{font-size:35px}body[data-hub="survival"] .feature-content,body[data-hub="voxel"] .feature-content{padding:24px}}
@media(prefers-reduced-motion:reduce){.survival-guide nav button{transition:none}}
''')
print('Survival extension installed with the existing catalog and personal state preserved.')
