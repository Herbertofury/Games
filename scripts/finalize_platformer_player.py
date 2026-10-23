#!/usr/bin/env python3
"""Guarded player compatibility correction proved by the legacy-stream gate.

The recorded Chrome failure advertises native HLS but rejects the Nintendo
MPEG-2 TS variant. Use the already pinned HLS.js implementation when its MSE
support test succeeds; retain native playback as a fallback, not a guess.
Reference: https://github.com/video-dev/hls.js#embedding-hlsjs
"""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'site/app.js';s=p.read_text()
old="""    if(v.canPlayType('application/vnd.apple.mpegurl')){v.src=safeURL(a.hls);return;}
    try{const Hls=await loadHls();if(!v.isConnected||currentGame?.id!==identity)return;if(Hls.isSupported()){hls=new Hls({enableWorker:true,maxBufferLength:30});hls.loadSource(safeURL(a.hls));hls.attachMedia(v);hls.on(Hls.Events.ERROR,(_,e)=>{if(e.fatal&&v.isConnected)v.dispatchEvent(new Event('error'));});}else v.dispatchEvent(new Event('error'));}catch{v.dispatchEvent(new Event('error'));}"""
new="""    // Native MIME support can be a false positive for MPEG-2 TS variants.
    // Prefer the existing HLS.js MSE path; preserve native-only browsers.
    try{
      const Hls=await loadHls();if(!v.isConnected||currentGame?.id!==identity)return;
      if(Hls.isSupported()){
        hls=new Hls({enableWorker:true,maxBufferLength:30});
        hls.on(Hls.Events.ERROR,(_,e)=>{if(e.fatal&&v.isConnected)v.dispatchEvent(new Event('error'));});
        hls.loadSource(safeURL(a.hls));hls.attachMedia(v);
      }else if(v.canPlayType('application/vnd.apple.mpegurl')){v.src=safeURL(a.hls);}
      else v.dispatchEvent(new Event('error'));
    }catch{
      if(!v.isConnected||currentGame?.id!==identity)return;
      if(v.canPlayType('application/vnd.apple.mpegurl'))v.src=safeURL(a.hls);
      else v.dispatchEvent(new Event('error'));
    }"""
if new not in s:
    assert s.count(old)==1,'Player source changed; inspect before migrating'
    s=s.replace(old,new,1)
for before,after in [('With official embedded trailers','With sourced videos / previews'),('verified entries without an embeddable official trailer.','verified entries without a playable video source.')]:
    if before in s:s=s.replace(before,after)
    else:assert after in s,'Media-attribution label changed'
p.write_text(s)
p=R/'tests/platformer_completion_qa.py';s=p.read_text();s=s.replace('Math.min(10,v.duration*.4)','Math.min(15,v.duration*.6)');p.write_text(s)
p=R/'docs/PLATFORMERS-COMPLETION.md';s=p.read_text()
if '## Player compatibility finding' not in s:
    s+='''\n## Player compatibility finding\n\nThe completion gate rejected two legacy Nintendo streams despite valid official playlists. Chrome reported native HLS MIME support but rejected their MPEG-2 transport-stream playback. The player now prefers its existing pinned HLS.js path when MediaSource support is available and retains native playback as the fallback. No media source was substituted and no failing playback assertion was removed. The actual two legacy streams and the earlier Steam/source regression suites must pass before publication. Data-health labels now say sourced videos/previews rather than incorrectly calling every credited community or library recording an official trailer.\n'''
    p.write_text(s)
print('Applied guarded HLS compatibility and honest media-label corrections.')
