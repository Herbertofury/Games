/* TEST FIXTURE ONLY. Production never imports this file or bypasses Steam. */
import {createServer} from 'node:http';
import {createApp,configuration} from '../services/steam-sync/server.mjs';
let privateOwned=false;
const config={...configuration({NODE_ENV:'development',PUBLIC_BASE_URL:'http://127.0.0.1:8792',APP_URL:'http://127.0.0.1:8791/',STEAM_WEB_API_KEY:'TEST-FIXTURE-ONLY'}),syncCooldown:0};
const handler=createApp({config,fetchImpl:async(url,init)=>{
 if(url==='https://steamcommunity.com/openid/login')return new Response(new URLSearchParams(init.body).get('openid.sig')==='fixture-signature'?'is_valid:true\n':'is_valid:false\n');
 if(url.includes('GetOwnedGames'))return Response.json(privateOwned?{response:{}}:{response:{game_count:3,games:[{appid:504230,playtime_forever:0},{appid:367520,playtime_forever:120},{appid:1145360}]}});
 return Response.json({response:{items:[{appid:1533420,priority:3},{appid:2365810,priority:0}]}});
}});
const server=createServer(async(req,res)=>{
 if(req.url==='/test/privacy'){privateOwned=true;res.end('ok');return;}
 const parts=[];for await(const p of req)parts.push(p);
 const r=await handler(new Request(new URL(req.url,config.publicOrigin),{method:req.method,headers:req.headers,...(['GET','HEAD'].includes(req.method)?{}:{body:Buffer.concat(parts)})}));
 res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));
});
server.listen(8792,'127.0.0.1');
