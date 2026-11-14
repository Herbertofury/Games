const {test}=require('node:test'),assert=require('node:assert/strict');
const {readText}=require('../site/steam-response.js');
function response(chunks,{failCancel=false}={}){
 let index=0,cancelled=0;
 const body=new ReadableStream({pull(c){if(index<chunks.length)c.enqueue(chunks[index++]);else c.close();},cancel(){cancelled++;if(failCancel)throw Error('cancel failure');}});
 return {body,pulls:()=>index,cancelled:()=>cancelled};
}
test('Over-limit response cancels before consuming the whole source and releases lock',async()=>{
 const r=response(Array.from({length:100},()=>new Uint8Array(4096)));
 await assert.rejects(readText(r,8192),/too large/);assert.equal(r.cancelled(),1);assert.ok(r.pulls()<=4);assert.equal(r.body.locked,false);
});
test('Exact limit accepted; UTF-8 characters and BOM survive arbitrary chunks like Response.text',async()=>{
 const bytes=new TextEncoder().encode('\ufeff{"name":"é😀"}');
 const r=response([...bytes].map(b=>Uint8Array.of(b)));
 assert.equal(await readText(r,bytes.length),await new Response(bytes).text());assert.equal(r.cancelled(),0);assert.equal(r.body.locked,false);
});
test('Limit counts bytes, not UTF-16 string length',async()=>{
 await assert.rejects(readText(new Response('😀😀'),7),/too large/);
 assert.equal(await readText(new Response('😀😀'),8),'😀😀');
});
test('Cancellation error cannot mask oversized-response diagnosis',async()=>{
 const r=response([new Uint8Array(20)],{failCancel:true});await assert.rejects(readText(r,1),/too large/);assert.equal(r.body.locked,false);
});
test('Network failure releases lock and is not converted to success',async()=>{
 const body=new ReadableStream({start(c){c.error(Error('network failed'));}});await assert.rejects(readText({body}),/network failed/);assert.equal(body.locked,false);
});
test('Empty body, zero limit and invalid limits handled explicitly',async()=>{
 assert.equal(await readText(new Response(null),0),'');assert.equal(await readText(new Response(''),0),'');
 for(const n of [-1,NaN,Infinity,1.5,'4'])await assert.rejects(readText(new Response(''),n),/Invalid/);
});
