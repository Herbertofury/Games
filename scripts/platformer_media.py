"""Additive media evidence: no identity, release, score or artwork replacement."""
from __future__ import annotations
import copy,re,urllib.parse

ALLOWED_FIELDS={'trailers','sources','mediaEvidence'}
FORMATS=('youtube','mp4','webm','hls')

def apply_reviewed_media(item,extra):
    if not extra:return copy.deepcopy(item)
    assert set(extra)<=ALLOWED_FIELDS, 'Media overlay cannot replace game facts'
    g=copy.deepcopy(item)
    for video in extra.get('trailers',[]):
        assert video.get('verified') is True and isinstance(video.get('official'),bool)
        assert video.get('credit') and video.get('verifiedAt') and video.get('sourceUrl')
        keys=[k for k in FORMATS if video.get(k)]
        assert len(keys)==1,'A reviewed video must have one unambiguous media source'
        if keys[0]=='youtube':assert re.fullmatch('[A-Za-z0-9_-]{11}',video['youtube'])
        else:
            url=urllib.parse.urlsplit(video[keys[0]])
            assert url.scheme=='https' and url.netloc,'Unsafe media URL'
        assert video['sourceUrl'].startswith('https://')
        if video.get('captureSha256'):
            assert not video['official'] and video.get('captureKind')=='Library-captured public browser preview'
            assert re.fullmatch('[a-f0-9]{64}',video['captureSha256'])
    def key(v):return next((v[k] for k in FORMATS if v.get(k)),v.get('sourceUrl'))
    g['trailers']=list({key(v):copy.deepcopy(v) for v in g.get('trailers',[])+extra.get('trailers',[])}.values())
    for source in extra.get('sources',[]):assert source.get('verified') is True and source['url'].startswith('https://')
    g['sources']=list({s['url']:copy.deepcopy(s) for s in g.get('sources',[])+extra.get('sources',[])}.values())
    g['platformerMediaEvidence']=copy.deepcopy(extra.get('mediaEvidence',{}))
    if any(any(v.get(k) for k in FORMATS) for v in g['trailers']):
        missing_prefixes=('No embeddable trailer returned','No independently parsed embedded trailer','No independently collected playable stream')
        g['warnings']=[w for w in g.get('warnings',[]) if not w.startswith(missing_prefixes)]
    return g
