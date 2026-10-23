#!/usr/bin/env python3
"""Apply researched edition corrections without overwriting collected metadata."""
import datetime as dt,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    path=ROOT/'data/shooters-external.json'
    if not path.exists():raise SystemExit('Install shooter sources first.')
    data=json.loads(path.read_text());before=json.dumps(data,sort_keys=True)
    checked='2026-10-23'
    for g in data['items']:
        if g['id']=='external:ashes-blackwater':
            u='https://www.moddb.com/mods/ashes-2063/downloads/ashes-blackwater'
            g['kind']='Free standalone / mod'
            g['requirements']='The June 20, 2026 v1.5 download is packaged as a standalone. Extract it and use its included launcher .bat. Hardcore mode requires the supplied GZDoom/config and its launcher. Earlier releases used a different setup.'
            g['updateNote']='Version 1.5, updated June 20, 2026, adopts a standalone package. Six remixed Afterglow/Hard Reset maps form a hub, rather than six newly made maps.'
            if g.get('mediaPage')!=u:
                g['mediaPage']=u
                for k in ['mediaCheckedAt','mediaPageHash']:g.pop(k,None)
            g['sources']=list({s['url']:s for s in g.get('sources',[])+[{'provider':'ModDB creator release notes','url':u,'verified':True,'lastChecked':checked}]}.values())
        elif g['id']=='external:total-chaos-original':
            u='https://www.moddb.com/mods/total-chaos/downloads/total-chaos-directors-cut-140'
            g['requirements']='Original free GZDoom Director\'s Cut 1.40, not the separate Unreal Engine remake. The official package includes GZDoom and does not require Total Chaos 1.0 or DOOM2.WAD.'
            if g.get('mediaPage')!=u:
                g['mediaPage']=u
                for k in ['mediaCheckedAt','mediaPageHash']:g.pop(k,None)
            g['storefronts']=list({s['url']:s for s in g.get('storefronts',[])+[{'provider':'ModDB','url':u,'kind':'download','verified':True,'lastChecked':checked}]}.values())
            g['sources']=list({s['url']:s for s in g.get('sources',[])+[{'provider':'ModDB original Director\'s Cut','url':u,'verified':True,'lastChecked':checked}]}.values())
    if json.dumps(data,sort_keys=True)!=before:
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print('Applied researched edition corrections.')
    else:print('Edition corrections already current.')
if __name__=='__main__':main()
