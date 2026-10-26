import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import model from '../site/steam-model.js';
test('Signed-out Steam data is rejected even when it has cached IDs',()=>{
 assert.throws(()=>model.importSnapshot({bLoggedIn:false,rgOwnedApps:[504230],rgWishlist:[1533420]}),/signed out/);
});
test('GameSync stable keys and source IDs remain usable without platformId',()=>{
 const s=model.importSnapshot({games:{one:{platform:'steam',key:'steam:504230'},two:{platform:'steam',sources:[{platform:'steam',platformId:'367520'}],status:'wishlist'}}});
 assert.equal(s.tracked[0].appid,504230);assert.equal(s.wishlist.items[0].appid,367520);
});
test('Official widget is created only by explicit trusted click and never pretends to sync',()=>{
 const s=readFileSync(new URL('../site/steam-wishlist.js',import.meta.url),'utf8');
 assert.ok(s.includes('if(!valid(g)||!event.isTrusted)return;'));
 assert.ok(s.includes('https://store.steampowered.com/widget/${id}/?l=english'));
 assert.ok(s.includes("frame.referrerPolicy='no-referrer'"));
 assert.ok(s.includes('never by assuming a widget click succeeded'));
 assert.equal(s.includes('GamesSteamApplyWishlist'),false);
});
