import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createApp, configuration } from './server.mjs';
const ORIGIN='https://herbertofury.github.io', BASE='https://sync.example.test';
const SECRET='TEST-KEY-NOT-A-REAL-KEY', ID='76561198000000001', NS='http://specs.openid.net/auth/2.0';
const verifier='a'.repeat(43), state='b'.repeat(43), digest=s=>createHash('sha256').update(s).digest('base64url');
function fixture(options={}){
 let clock=Date.parse('2026-10-25T18:00:00Z'), calls=[];
 const config={...configuration({PUBLIC_BASE_URL:BASE,APP_URL:ORIGIN+'/Games/',STEAM_WEB_API_KEY:SECRET}),...options.config};
 const fetchImpl=async(url,init)=>{calls.push({url,init});if(options.fetch)return options.fetch(url,init);
  if(url.includes('openid'))return new Response('ns:'+NS+'\nis_valid:true\n');
  if(url.includes('GetOwnedGames'))return Response.json({response:{game_count:1,games:[{appid:504230,playtime_forever:0}]}});
  return Response.json({response:{items:[{appid:1533420,priority:1}]}});
 };
 const handle=createApp({config,fetchImpl,now:()=>clock});
 return {handle,calls,config,advance:n=>clock+=n,now:()=>clock};
}
function request(path,{method='GET',origin=ORIGIN,body,headers={}}={}){
 return new Request(BASE+path,{method,headers:{...(origin?{Origin:origin}:{}),...(body?{'Content-Type':'application/json'}:{}),...headers},...(body?{body:JSON.stringify(body)}:{})});
}
async function attempt(f){
 const r=await f.handle(request(`/auth/start?challenge=${digest(verifier)}&client_state=${state}`));assert.equal(r.status,302);
 const login=new URL(r.headers.get('location'));assert.equal(login.origin,'https://steamcommunity.com');
 const callback=new URL(login.searchParams.get('openid.return_to'));
 for(const[k,v]of Object.entries({ns:NS,mode:'id_res',op_endpoint:'https://steamcommunity.com/openid/login',claimed_id:'https://steamcommunity.com/openid/id/'+ID,identity:'https://steamcommunity.com/openid/id/'+ID,return_to:callback.href,response_nonce:new Date(f.now()).toISOString().replace('.000','')+'unique',assoc_handle:'test',signed:'op_endpoint,claimed_id,identity,return_to,response_nonce,assoc_handle',sig:'test-signature'}))callback.searchParams.set('openid.'+k,v);
 return {callback,cookie:r.headers.get('set-cookie').split(';')[0]};
}
async function callback(f,a){return f.handle(new Request(a.callback,{headers:{Cookie:a.cookie}}));}
async function authenticate(f){const a=await attempt(f),r=await callback(f,a),html=await r.text();const code=JSON.parse(html.match(/postMessage\((\{.*?\}),/)[1]).code;assert.ok(code);
 const exchange=await f.handle(request('/auth/exchange',{method:'POST',body:{code,verifier}}));assert.equal(exchange.status,200);return {a,code,...await exchange.json()};}
test('Configuration rejects insecure nonlocal and credentialed URLs',()=>{
 for(const url of ['http://example.com','https://user:pass@example.com','https://x/a','https://x/?key=secret'])assert.throws(()=>configuration({PUBLIC_BASE_URL:url}));
 assert.equal(configuration({PUBLIC_BASE_URL:BASE}).appOrigin,ORIGIN);
});
test('Health contains capabilities, no key, and cache is disabled',async()=>{
 const f=fixture(),r=await f.handle(request('/health'));assert.equal(r.headers.get('cache-control'),'no-store, max-age=0');const s=await r.text();assert.equal(s.includes(SECRET),false);assert.ok(s.includes('games-steam-sync'));
});
test('Valid OpenID -> one-time PKCE grant -> short-lived scoped session -> independent lists',async()=>{
 const f=fixture(),a=await authenticate(f);assert.equal(a.steamId,ID);
 const r=await f.handle(request('/sync',{method:'POST',body:{steamid:'76561198000000002'},headers:{Authorization:'Bearer '+a.token}}));assert.equal(r.status,200);const raw=await r.json();assert.equal(raw.steamId,ID);assert.equal(raw.owned.items[0].appid,504230);assert.equal(raw.wishlist.items[0].appid,1533420);
 const upstream=f.calls.find(x=>x.url.includes('GetOwnedGames'));const input=JSON.parse(new URL(upstream.url).searchParams.get('input_json'));assert.equal(input.steamid,ID);assert.equal(JSON.stringify(raw).includes(SECRET),false);
 assert.equal(f.calls[0].init.redirect,'error');assert.ok(f.calls[0].init.body.includes('openid.mode=check_authentication'));
});
test('Callback requires same-browser cookie and correct state',async()=>{
 const f=fixture(),a=await attempt(f);const r=await f.handle(new Request(a.callback));assert.equal(r.status,400);assert.equal(f.calls.length,0);
});
for(const[field,value]of [['op_endpoint','https://evil.test'],['identity','https://steamcommunity.com/openid/id/76561198000000002'],['return_to','https://evil.test'],['signed','identity,claimed_id'],['response_nonce','2020-01-01T00:00:00Zold'],['ns','evil']])test('Rejects forged '+field,async()=>{
 const f=fixture(),a=await attempt(f);a.callback.searchParams.set('openid.'+field,value);const text=await(await callback(f,a)).text();assert.ok(text.includes('could not be verified'));assert.equal(f.calls.length,0);
});
test('Invalid Steam signature cannot become a session',async()=>{
 const f=fixture({fetch:async()=>new Response('is_valid:false\n')}),a=await attempt(f);const text=await(await callback(f,a)).text();assert.ok(!text.includes('"code":'));
});
test('Duplicate parameters and callback replay are rejected',async()=>{
 const f=fixture(),a=await attempt(f);a.callback.searchParams.append('openid.mode','id_res');assert.ok((await(await callback(f,a)).text()).includes('could not be verified'));assert.equal((await callback(f,a)).status,400);
});
test('Wrong verifier and reused authorization codes fail',async()=>{
 const f=fixture(),a=await attempt(f),html=await(await callback(f,a)).text(),code=JSON.parse(html.match(/postMessage\((\{.*?\}),/)[1]).code;
 assert.equal((await f.handle(request('/auth/exchange',{method:'POST',body:{code,verifier:'z'.repeat(43)}}))).status,401);
 assert.equal((await f.handle(request('/auth/exchange',{method:'POST',body:{code,verifier}}))).status,200);
 assert.equal((await f.handle(request('/auth/exchange',{method:'POST',body:{code,verifier}}))).status,401);
});
test('Session is required, expires, and is revoked on logout',async()=>{
 const f=fixture();assert.equal((await f.handle(request('/sync',{method:'POST',body:{}}))).status,401);const a=await authenticate(f);
 assert.equal((await f.handle(request('/logout',{method:'POST',headers:{Authorization:'Bearer '+a.token}}))).status,200);
 assert.equal((await f.handle(request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+a.token}}))).status,401);
 const g=fixture(),b=await authenticate(g);g.advance(3600001);assert.equal((await g.handle(request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+b.token}}))).status,401);
});
test('Cross-origin POST and wildcard CORS are prohibited',async()=>{
 const f=fixture();for(const origin of ['https://evil.test','null',null]){const r=await f.handle(request('/auth/exchange',{method:'POST',origin,body:{}}));assert.equal(r.status,403);assert.equal(r.headers.get('access-control-allow-origin'),null);}
 const r=await f.handle(request('/sync',{method:'OPTIONS'}));assert.equal(r.status,204);assert.equal(r.headers.get('access-control-allow-origin'),ORIGIN);
});
test('Private library does not block an available wishlist',async()=>{
 const f=fixture({fetch:async url=>url.includes('openid')?new Response('is_valid:true\n'):Response.json(url.includes('GetOwnedGames')?{response:{}}:{response:{items:[{appid:1}]}})}),a=await authenticate(f);
 const raw=await(await f.handle(request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+a.token}}))).json();assert.equal(raw.owned.status,'unavailable');assert.equal(raw.wishlist.status,'ok');
});
test('Missing operator API key is reported, not solicited from a visitor',async()=>{
 const f=fixture({config:{apiKey:''}}),a=await authenticate(f);const raw=await(await f.handle(request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+a.token}}))).json();assert.equal(raw.owned.status,'unavailable');assert.ok(raw.owned.message.includes('operator'));assert.equal(f.calls.some(x=>x.url.includes('GetOwnedGames')),false);
});
test('Sync cooldown and storage capacity are bounded',async()=>{
 const f=fixture(),a=await authenticate(f),r=()=>request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+a.token}});assert.equal((await f.handle(r())).status,200);const second=await f.handle(r());assert.equal(second.status,429);assert.equal(second.headers.get('retry-after'),'60');
 const g=fixture({config:{maxEntries:1}});await attempt(g);assert.equal((await g.handle(request(`/auth/start?challenge=${digest(verifier)}&client_state=${state}`))).status,503);
});
test('Network errors never leak API keys or upstream URLs',async()=>{
 const f=fixture({fetch:async url=>{if(url.includes('openid'))return new Response('is_valid:true\n');throw Error(url);}}),a=await authenticate(f);const text=await(await f.handle(request('/sync',{method:'POST',body:{},headers:{Authorization:'Bearer '+a.token}}))).text();assert.equal(text.includes(SECRET),false);assert.equal(text.includes('api.steampowered.com'),false);
});
