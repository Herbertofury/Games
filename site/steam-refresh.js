/* Scheduling only: never stores credentials or changes membership. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SteamRefreshPolicy=api;})(typeof window==='object'?window:globalThis,function(){
 'use strict';
 const COOLDOWN=65000, PERIOD=300000, MAX_BACKOFF=900000;
 function create(now=Date.now){
  let last=null, next=0, failures=0;
  return Object.freeze({
   reset(){last=null;next=0;failures=0;},
   due({connected,visible,online,busy,pending,enabled,reason='periodic'}){
    if(!connected||!visible||!online||busy||pending||!enabled)return false;
    const time=now();if(!Number.isFinite(time)||time<next)return false;
    return last===null||time-last>=(reason==='return'?COOLDOWN:PERIOD);
   },
   started(){last=now();next=last+COOLDOWN;},
   finished(ok){if(ok){failures=0;next=Math.max(next,now()+COOLDOWN);}else{failures=Math.min(failures+1,5);next=Math.max(next,now()+Math.min(MAX_BACKOFF,60000*2**failures));}},
  });
 }
 return Object.freeze({create,COOLDOWN,PERIOD,MAX_BACKOFF});
});
