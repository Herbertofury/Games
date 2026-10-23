#!/usr/bin/env python3
"""Recover approved evidence files only, then pin preview URLs to their commit.

The artifact is not executed or unpacked over source. Only its reviewed JSON
and two explicitly named/hash-checked WebM files can enter the repository.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,shutil,subprocess
R=pathlib.Path(__file__).resolve().parents[1]

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--evidence',type=pathlib.Path,required=True);ap.add_argument('--assets-only',action='store_true');args=ap.parse_args();e=args.evidence.resolve()
 approval=json.loads((R/'data/platformers-preview-approval.json').read_text())
 incoming=e/'data/platformers-media-reviewed.json'
 assert digest(incoming)==approval['reviewedMediaSha256'],'Different metadata than the reviewed artifact'
 media=json.loads(incoming.read_text());assert len(media['overrides'])==18,'Expected eighteen independently sourced videos'
 proposals=json.loads((e/'qa/platformer-video-resolution/browser-preview-proposals.json').read_text());by={g['id']:g for g in json.loads((R/'data/platformers-external.json').read_text())['items']}
 for approved in approval['previews']:
  ident=approved['id'];proposal=next(x for x in proposals if x['id']==ident)
  assert not proposal.get('error') and approved['visualReviewPassed'] is True
  relative=pathlib.PurePosixPath(proposal['localPath']);assert not relative.is_absolute() and '..' not in relative.parts
  assert str(relative)==approved['path'] and str(relative).startswith('site/assets/platformer-previews/') and relative.suffix=='.webm'
  src=e/relative;assert src.is_file() and src.stat().st_size<6000000
  assert digest(src)==approved['sha256']==proposal['sha256'],'Unreviewed browser recording'
  dest=R/relative;dest.parent.mkdir(parents=True,exist_ok=True)
  if args.assets_only:shutil.copyfile(src,dest);continue
  assert dest.is_file() and digest(dest)==approved['sha256']
  revision=subprocess.check_output(['git','log','-1','--format=%H','--',str(relative)],cwd=R,text=True).strip();assert re.fullmatch('[a-f0-9]{40}',revision)
  tracked=subprocess.check_output(['git','show',revision+':'+str(relative)],cwd=R);assert hashlib.sha256(tracked).hexdigest()==approved['sha256']
  g=by[ident];source=proposal['sourceUrl'];video={'name':g['name']+' — public browser gameplay preview','webm':'https://raw.githubusercontent.com/Herbertofury/Games/'+revision+'/'+str(relative),'poster':g['image'],'sourceUrl':source,'watchUrl':source,'credit':'Games library capture of the creator-published PICO-8 browser build; not an official trailer','official':False,'verified':True,'verifiedAt':approval['reviewedAt'],'captureKind':'Library-captured public browser preview','capturePath':str(relative),'captureSha256':approved['sha256'],'editionNote':'A short recorded interaction with the exact free browser release. This is not the commercial Celeste game, a full playthrough, or a claim of comprehensive hands-on review.'}
  media['overrides'][ident]={'trailers':[video],'sources':[{'provider':'Creator browser build','url':source,'verified':True,'lastChecked':approval['reviewedAt']},{'provider':'Exact played public build','url':proposal['buildUrl'],'verified':True,'lastChecked':approval['reviewedAt']}],'mediaEvidence':{'sourceUrl':source,'buildUrl':proposal['buildUrl'],'captureSha256':approved['sha256'],'captureRevision':revision,'visualReview':approved['visualReview'],'reviewedAt':approval['reviewedAt']}}
 if args.assets_only:
  print('Only approved capture assets copied; commit them before building pinned URLs.');return
 assert len(media['overrides'])==20
 media['checkedAt']=max(media['checkedAt'],approval['reviewedAt']);(R/'data/platformers-media-reviewed.json').write_text(json.dumps(media,ensure_ascii=False,indent=2)+'\n')
 report={'reviewedAt':approval['reviewedAt'],'resolvedRecords':20,'thirdPartySourceVideos':18,'libraryCapturedPreviews':2,'evidenceRun':approval['sourceRunId'],'evidenceArtifactSha256':approval['artifactSha256'],'scope':'Metadata resolution and visual capture approval; actual library playback has a separate browser report.'}
 (R/'data/platformers-completion-report.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Twenty missing-video records installed through the additive overlay.')
if __name__=='__main__':main()
