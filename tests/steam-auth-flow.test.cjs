const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../site/steam-sync.js'),'utf8');
// Execute the real message listener with isolated UI/transport dependencies.
const start=source.indexOf("  window.addEventListener('message',async event=>{");
const end=source.indexOf('  async function sync()',start);
assert.ok(start>=0&&end>start);
function setup(){
 let reject,resolve,listener;
 const request=new Promise((yes,no)=>{resolve=yes;reject=no;});
 const flow={popup:{},state:'fixture-state',timer:1};
 const ctx={pending:flow,epoch:0,message:'unchanged',session:null,window:{addEventListener:(name,fn)=>{listener=fn;}},
  service:()=> 'https://bridge.example',clearInterval(){},api:()=>request,draw(){},
  clearPending(){ctx.pending=null;},M:{steamid:()=> '76561198000000001'}};
 vm.runInNewContext(source.slice(start,end),ctx);
 const running=listener({origin:'https://bridge.example',source:flow.popup,data:{type:'games-steam-auth',state:flow.state,code:'a'.repeat(43)}});
 return {ctx,flow,reject,resolve,running};
}
test('obsolete exchange failure cannot clear a newer sign-in',async()=>{
 const s=setup(),newer={state:'new-flow'};s.ctx.pending=newer;s.ctx.epoch++;s.ctx.message='new sign-in';
 s.reject(new Error('old exchange failed'));await s.running;
 assert.equal(s.ctx.pending,newer);assert.equal(s.ctx.message,'new sign-in');
});
test('failure after disconnect cannot replace cleared feedback',async()=>{
 const s=setup();s.ctx.pending=null;s.ctx.epoch++;s.ctx.message='cleared';
 s.reject(new Error('old exchange failed'));await s.running;
 assert.equal(s.ctx.pending,null);assert.equal(s.ctx.message,'cleared');
});
test('current exchange failure still clears its flow and reports error',async()=>{
 const s=setup();s.reject(new Error('current exchange failed'));await s.running;
 assert.equal(s.ctx.pending,null);assert.equal(s.ctx.message,'current exchange failed');
});
test('obsolete exchange success remains ignored',async()=>{
 const s=setup(),newer={state:'new-flow'};s.ctx.pending=newer;s.ctx.epoch++;
 s.resolve({token:'a'.repeat(43)});await s.running;
 assert.equal(s.ctx.pending,newer);assert.equal(s.ctx.session,null);
});
