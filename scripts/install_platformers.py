#!/usr/bin/env python3
"""Guarded, idempotent migration of the existing library, never a replacement app."""
from __future__ import annotations
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]

def patch(path,old,new):
 p=ROOT/path;s=p.read_text()
 if new in s:return
 if s.count(old)!=1:raise RuntimeError(f'{path}: expected one known source anchor, found {s.count(old)}; refusing an unreviewed overwrite')
 p.write_text(s.replace(old,new,1))

patch('scripts/catalog_model.py','from source_links import normalized_links','from source_links import normalized_links\nfrom platformer_model import merge_platformers,complete_platformer_metadata')
patch('scripts/catalog_model.py',"    out=sorted(games.values(),key=lambda g:g['name'].casefold())","    games=merge_platformers(games,ROOT)\n    out=sorted(games.values(),key=lambda g:g['name'].casefold())")
patch('scripts/catalog_model.py','    return c\n','    return complete_platformer_metadata(c,ROOT)\n')
patch('scripts/catalog_model.py',"if g.get('verification')!='verified' or g.get('fit') is None:return None","if g.get('verification')!='verified' or g.get('fit') is None or g.get('comingSoon'):return None")
patch('scripts/build.py','from wiki_builder import build_wiki','from wiki_builder import build_wiki\nfrom platformer_study import build_platformer_wiki')
patch('scripts/build.py',"app=source('app.js').replace","app=(source('app.js')+'\\n'+source('platformers.js')).replace")
patch('scripts/build.py',".replace('/*__CSS__*/',source('styles.css'))",".replace('/*__CSS__*/',source('styles.css')+'\\n'+source('platformers.css'))")
patch('scripts/build.py','    build_wiki(ROOT,catalog)\n','    build_wiki(ROOT,catalog)\n    build_platformer_wiki(ROOT,catalog)\n')
patch('scripts/wiki_builder.py',"else '[Roguelites](Roguelites)' for h in g.get('hubs',[])","else '[Platformers](Platformers)' if h=='Platformers' else '[Roguelites](Roguelites)' for h in g.get('hubs',[])")
patch('site/app.js',"g.name,g.seedName,g.summary,g.curatorWhy,g.requirements,g.collection","g.name,g.seedName,g.summary,g.curatorWhy,g.platformerWhy,g.platformerCaution,g.platformerInfo?.focus,g.requirements,g.collection")
patch('site/app.js',"if(g.verification!=='verified'||g.fit==null)return null","if(g.verification!=='verified'||g.fit==null||g.comingSoon)return null")
patch('scripts/refresh.py',"old={str(g['seedId']):g for g in json.loads(target.read_text()).get('items',[])}","old={str(g.get('seedId') or g.get('appid')):g for g in json.loads(target.read_text()).get('items',[]) if g.get('seedId') or g.get('appid')}")
patch('scripts/platformer_model.py',"'videos':sum(any(t.get(k) for k in ['mp4','webm','hls','youtube']) for g in rows for t in g.get('trailers',[]))","'videos':sum(any(any(t.get(k) for k in ['mp4','webm','hls','youtube']) for t in g.get('trailers',[])) for g in rows)")
patch('site/platformers.js',' const featuredBefore=featuredGame'," const originalBestLabel=$('[data-preset=\"best\"] small').textContent,originalNewLabel=$('[data-preset=\"new\"] small').textContent;\n const featuredBefore=featuredGame")
patch('site/platformers.js','  if(!active)return;','  if(!active){$(\'[data-preset="best"] small\').textContent=originalBestLabel;$(\'[data-preset="new"] small\').textContent=originalNewLabel;return;}')
# Preserve exact original membership assertions, but stop treating the library
# as permanently frozen at the number of records in an earlier release.
patch('tests/test_multiplatform.py','self.assertEqual(len(seeds),170)','self.assertGreaterEqual(len(seeds),170);self.assertEqual(len(seeds),len({s["appid"] for s in seeds}))')
patch('tests/test_rts.py',"self.assertEqual(len(self.rows),130);self.assertEqual(len(self.data['items']),448);self.assertEqual(len({g['id'] for g in self.data['items']}),448)","self.assertEqual(len(self.rows),130);self.assertEqual(len(self.data['items']),self.data['build']['inputCount']);self.assertEqual(len({g['id'] for g in self.data['items']}),len(self.data['items']))")
patch('tests/test_rts.py',"self.assertEqual(sum('Roguelites' in g['hubs'] for g in self.data['items']),170)","self.assertGreaterEqual(sum('Roguelites' in g['hubs'] for g in self.data['items']),171)")
patch('tests/multiplatform_qa.py',"check('All 170 original recommendations remain in their genre',len(page.evaluate('GamesTest.filtered'))==170)","check('All canonical roguelite recommendations remain in their genre',len(page.evaluate('GamesTest.filtered'))==sum('Roguelites' in g.get('hubs',[]) for g in by.values()))")
patch('tests/rts_qa.py',"for hub,count in [('Roguelites',170),('Boomer shooters',150),('Real-time strategy',130)]:","for hub,count in [(h,catalog['build']['hubCounts'][h]) for h in ['Roguelites','Boomer shooters','Real-time strategy']]:")
patch('tests/genre_inline.py',"assert page.locator('.game-card').count()==170","assert page.locator('.game-card').count()==page.evaluate(\"CATALOG.build.hubCounts.Roguelites\")")
# New data and modules must reach the same existing publishing gate. No tests
# are removed, and native wiki/Pages publication still occurs only after QA.
patch('.github/workflows/publish.yml',"paths: ['site/**'","paths: ['data/platformers-*','scripts/platformer*.py','scripts/collect_platformers.py','docs/PLATFORMERS-STUDY.md','site/**'")
patch('.github/workflows/publish.yml','          node --check site/app.js','          node --check site/app.js\n          node --check site/platformers.js')
patch('.github/workflows/publish.yml','          python3 tests/rts_qa.py','          python3 tests/rts_qa.py\n          python3 tests/platformers_qa.py')
patch('.github/workflows/publish.yml','          cp qa/rts-*.png docs/qa/','          cp qa/rts-*.png docs/qa/\n          cp qa/platformers-*.png docs/qa/')
patch('.github/workflows/publish.yml',"--title 'Games - Living Library'","--title 'Games - Living Library with Platformers'")
# Keep historic discovery conventions, but document the new canonical sources.
p=ROOT/'docs/UPDATING.md';s=p.read_text()
if '## Platformer study' not in s:
 s+='''\n## Platformer study\n\nThe fourth hub shares the same application, canonical IDs, browser storage, wiki publisher and release pipeline. `data/platformers-seeds.tsv` is a discovery ledger, not a list of automatically endorsed games. `platformers-steam.json` contains exact-title-verified Steam snapshots; `platformers-external-seeds.json` contains manually reviewed console/creator identities and edition constraints. `platformers-editorial.tsv` holds individual editorial notes. The assembled record labels individual notes separately from subgenre study lenses.\n\nRun `python3 scripts/collect_platformers.py` for a paced incremental Steam refresh, or add `--force` to deliberately refresh all facts. Use `python3 scripts/platformer_extras.py` for exact-page external media; failed requests retain older media and expose gaps. No scheduler is installed. After source changes, run the standard build, all unit tests and `python3 tests/platformers_qa.py`. Do not use `prepare_platformers.py` or `install_platformers.py` as a general-purpose updater: they are guarded migration records.\n\nThe study deliberately includes clearly marked traversal hybrids. Nintendo and PlayStation hardware requirements are explicit. PC operating systems returned by Steam are not a complete console-port inventory. New store editions are not automatically new original games. Future entries have no purchase score; demos are separate links rather than silently substituted identities. Gem labels are an editorial shortlist constrained by reception/sample evidence, not an objective popularity measurement. Missing artwork or playable video is reported, never replaced with unrelated media.\n\nThe generated `wiki/Platformers*.md`, `data/platformers-study-report.json` and `data/platformers-index.csv` are derived from the same complete snapshot. The media atlas links every record, including honest gaps. GitHub Markdown cannot run embedded video players; the interactive HTML provides playback where a source stream exists. Publication is proved by the publishing workflow and its native-wiki/release/Pages reports, not merely by generated files.\n'''
 p.write_text(s)
p=ROOT/'README.md';s=p.read_text()
if '[Platformers]' not in s:s=s.replace('[Real-time strategy]','[Platformers](https://github.com/Herbertofury/Games/wiki/Platformers) | [Platformer study](https://github.com/Herbertofury/Games/wiki/Platformers-Study) | [Real-time strategy]',1)
a=s.find('The current source contains ');b=s.find('A store appearing twice',a)
if a>=0 and b>a:s=s[:a]+'The canonical source spans roguelites, shooters, real-time strategy and the researched platformer collection. Counts, overlaps and source coverage are generated from the current snapshot rather than frozen in this introduction. '+s[b:]
if '`data/platformers-seeds.tsv`' not in s:s=s.replace('- `data/catalog.json`','- `data/platformers-seeds.tsv`, `data/platformers-steam.json`, `data/platformers-external*.json`, and `data/platformers-editorial.tsv`: exact platformer identities, current source snapshots, console/creator editions, and individual editorial notes.\n- `docs/PLATFORMERS-STUDY.md`: the comparative study and discovery methodology.\n- `data/catalog.json`',1)
p.write_text(s)
print('Platformer integration migration applied; original application and persistence key retained.')
