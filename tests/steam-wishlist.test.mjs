import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
const source=readFileSync(new URL('../site/steam-wishlist.js',import.meta.url),'utf8');
test('Wishlist module is an official-page handoff, not an undocumented write client',()=>{
 for(const bad of ['addtowishlist','removefromwishlist','g_sessionID','credentials:','chrome.cookies','fetch('])assert.equal(source.includes(bad),false,bad);
 assert.ok(source.includes('https://store.steampowered.com/app/${id}/'));
 assert.ok(source.includes('Complete wishlist additions or removals on Steam'));
});
test('Actions require an exact Steam AppID and avoid opener access',()=>{
 assert.ok(source.includes('Number.isSafeInteger(g.appid)'));assert.ok(source.includes('rel="noopener noreferrer"'));
});
test('Wishlist handoff never pretends a remote write succeeded',()=>{
 assert.ok(source.includes('No Steam change is assumed.'));assert.equal(source.includes('GamesSteamApplyWishlist'),false);
});
test('Unreviewed cookie-based extension is excluded from this revision',()=>{
 assert.equal(existsSync(new URL('../extensions/steam-wishlist/background.mjs',import.meta.url)),false);
});
