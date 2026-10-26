const { test } = require('node:test');
const assert = require('node:assert/strict');
const M = require('../site/steam-model.js');
const base = overrides => M.normalize({schemaVersion:1,provider:'steam',steamId:'76561198000000001',...overrides},{imported:false});
const ok = ids => ({status:'ok',complete:true,checkedAt:'2026-10-25T00:00:00Z',items:ids});
test('AppIDs are exact unsigned integers; SteamIDs are not rounded numbers',()=>{
 for(const x of [0,-1,1.2,'1e3','1<script>',{},4294967296])assert.throws(()=>M.appid(x));
 assert.equal(M.appid('504230'),504230);
 assert.throws(()=>M.steamid(76561198000000001));assert.equal(M.steamid('76561198000000001'),'76561198000000001');
});
test('Missing/private owned data is not an empty library',()=>{
 for(const x of [{},{response:{}},{response:{games:[]}},{response:{game_count:2,games:[{appid:1}]}},{response:{game_count:2,games:[{appid:1},{appid:1}]}}])assert.throws(()=>M.ownedResponse(x));
 assert.equal(M.ownedResponse({response:{game_count:0}}).items.length,0);
});
test('Wishlist must be explicit, including a confirmed empty array',()=>{
 assert.throws(()=>M.wishlistResponse({response:{}}));assert.deepEqual(M.wishlistResponse({response:{items:[]}}).items,[]);
 assert.throws(()=>M.wishlistResponse({response:{items:[{appid:1},{appid:1}]}}));
});
test('Privacy failure preserves same-account last good data and dates',()=>{
 const old=base({owned:ok([{appid:504230,playtimeMinutes:10}]),wishlist:ok([{appid:1}])});
 const next=base({owned:{status:'unavailable',message:'private'},wishlist:ok([{appid:2}])});
 const merged=M.merge(old,next);assert.equal(merged.owned.items[0].appid,504230);assert.equal(merged.owned.stale,true);assert.equal(merged.owned.checkedAt,old.owned.checkedAt);assert.equal(merged.wishlist.items[0].appid,2);
});
test('Account switch never mixes another account library',()=>{
 const old=base({owned:ok([{appid:1}])});const next=base({steamId:'76561198000000002'});assert.equal(M.merge(old,next).owned.items.length,0);
});
test('Local import cannot authenticate, persist credentials or overwrite private notes',()=>{
 const raw={schemaVersion:1,provider:'steam',steamId:'76561198000000001',authenticated:true,token:'SECRET',steamApiKey:'SECRET',notes:{foo:'private'},owned:ok([{appid:1,token:'secret'}])};
 const out=M.importSnapshot(raw);assert.equal(out.source,'import');assert.equal(JSON.stringify(out).includes('SECRET'),false);assert.equal(JSON.stringify(out).includes('private'),false);assert.equal(out.authenticated,undefined);
});
test('Steam browser export handles owned and wishlist separately, without inventing playtime',()=>{
 const s=M.importSnapshot({rgOwnedApps:[504230,367520],rgWishlist:[1533420],steamLoginSecure:'discard'});
 assert.equal(s.owned.items[0].playtimeMinutes,null);assert.equal(s.wishlist.items[0].appid,1533420);assert.equal(s.steamLoginSecure,undefined);
 assert.throws(()=>M.importSnapshot({rgOwnedApps:[],rgWishlist:[]}));
});
test('GameSync records are tracked, not licenses, unless explicitly marked',()=>{
 const db={games:{one:{key:'steam:504230',platform:'steam',platformId:'504230',title:'<script>',hoursPlayed:2},two:{platform:'steam',platformId:'367520',status:'wishlist'},three:{platform:'gog',platformId:'123'}}};
 const s=M.importSnapshot(db);assert.equal(s.owned.status,'unknown');assert.deepEqual(s.tracked,[{appid:504230}]);assert.equal(s.wishlist.items[0].appid,367520);
 const own=M.importSnapshot(db,{treatTrackedAsOwned:true});assert.equal(own.owned.complete,false);assert.equal(own.owned.items[0].playtimeMinutes,120);
});
test('Unknown playtime is not zero and non-Steam titles are not guessed',()=>{
 const ix=M.index(base({owned:ok([{appid:1,playtimeMinutes:null},{appid:2,playtimeMinutes:0}])}));
 assert.equal(M.match({appid:1},'unplayed',ix),false);assert.equal(M.match({appid:2},'unplayed',ix),true);assert.equal(M.match({appid:null},'discover',ix),false);assert.equal(M.match({appid:3},'discover',ix),true);
 ix.completeOwned=false;assert.equal(M.match({appid:3},'discover',ix),false);
});
test('Partial import merges membership without claiming completeness',()=>{
 const old=M.importSnapshot({rgOwnedApps:[1],rgWishlist:[2]});const next=M.importSnapshot({games:{one:{platform:'steam',platformId:'3',owned:true},two:{platform:'steam',platformId:'4',status:'wishlist'}}});
 old.steamId=next.steamId='76561198000000001';
 const s=M.merge(old,next);assert.deepEqual(s.owned.items.map(x=>x.appid),[1,3]);assert.equal(s.owned.complete,false);
});
test('Malformed imports fail atomically; bad JSON fields are bounded',()=>{
 assert.throws(()=>M.importSnapshot({response:{game_count:2,games:[{appid:1},{appid:'bad'}]}}));
 assert.throws(()=>M.importSnapshot({schemaVersion:2,provider:'steam'}));
 assert.throws(()=>M.items(new Array(50001).fill(1),'owned'));
 assert.throws(()=>M.items([{appid:1,playtimeMinutes:-3}],'owned'));
});

test('Unbound imports are replacements, not guessed same-account merges',()=>{
 const old=M.importSnapshot({rgOwnedApps:[1],rgWishlist:[2]});
 const next=M.importSnapshot({games:{one:{platform:'steam',platformId:'3',owned:true}}});
 assert.deepEqual(M.merge(old,next).owned.items.map(x=>x.appid),[3]);
});
