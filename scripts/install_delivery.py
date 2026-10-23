#!/usr/bin/env python3
"""Install a hash-checked, text-only source delta. Never execute payload content."""
import base64,hashlib,json,lzma,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def install():
    manifest=json.loads((ROOT/'.delivery/shooters-manifest.json').read_text())
    blob=base64.b64decode(''.join((ROOT/f'.delivery/shooters-{i}.txt').read_text().strip() for i in range(manifest['parts'])),validate=True)
    assert sha(blob)==manifest['sha256'],'Delivery integrity mismatch'
    entries=json.loads(lzma.decompress(blob));prepared=[]
    for path,change in entries.items():
        rel=pathlib.PurePosixPath(path)
        assert not rel.is_absolute() and '..' not in rel.parts
        assert rel.parts[0] in {'site','scripts','tests','docs','data','requirements-dev.txt','README.md'}
        dest=ROOT/rel;old=dest.read_bytes() if dest.exists() else b''
        if sha(old)==change['sha256']:continue
        assert sha(old)==change['baseSha256'],f'Concurrent edit detected: {path}; reconcile instead of overwriting'
        lines=old.decode('utf-8').splitlines(keepends=True)
        for a,b,insert in reversed(change['operations']):lines[a:b]=insert
        new=''.join(lines).encode('utf-8');assert sha(new)==change['sha256'],path
        prepared.append((dest,new))
    # Validate every base before writing the first file.
    for dest,new in prepared:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(new)
    print('Verified source delta:',len(entries),'files;',len(prepared),'changed')
if __name__=='__main__':install()
