/* Bounded transport decoding only; no credentials, persistence or provider policy. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.SteamResponseReader=api;})(typeof window==='object'?window:globalThis,function(){
 'use strict';
 const MAX_BYTES=8000000;
 async function readText(response,limit=MAX_BYTES){
  if(!Number.isSafeInteger(limit)||limit<0)throw new TypeError('Invalid response byte limit');
  if(!response.body)return '';
  const reader=response.body.getReader(),decoder=new TextDecoder();
  let bytes=0;const parts=[];
  try{
   while(true){
    const {done,value}=await reader.read();if(done)break;
    bytes+=value.byteLength;
    if(bytes>limit){
     try{await reader.cancel('Steam response exceeded byte limit');}catch{}
     throw new Error('The Steam response was too large.');
    }
    parts.push(decoder.decode(value,{stream:true}));
   }
   parts.push(decoder.decode());return parts.join('');
  }finally{reader.releaseLock();}
 }
 return Object.freeze({readText,MAX_BYTES});
});
