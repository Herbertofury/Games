/* Official Steam handoff. OpenID is not a wishlist-write authorization. */
'use strict';
(function installSteamWishlistActions(){
  const previous={card,table,source:sourcePanel};
  const valid=g=>typeof g.appid==='number'&&Number.isSafeInteger(g.appid)&&g.appid>0&&g.appid<=4294967295;
  const notice=document.createElement('p');notice.className='steam-action-feedback';notice.setAttribute('role','status');notice.setAttribute('aria-live','polite');notice.hidden=true;
  $('.steam-library-strip').after(notice);
  const help=document.createElement('details');help.className='steam-wishlist-help';
  help.innerHTML='<summary>How Steam wishlist actions work</summary><p>Wishlist on Steam opens the exact official app page. Add or remove the game there using Steam\'s own controls, then refresh your snapshot here. A click on this site does not claim that Steam changed your wishlist.</p><p>Steam sign-in verifies identity; it does not grant wishlist-write permission. This site does not read Steam cookies, ask for passwords or API keys, or send undocumented account-changing requests.</p>';
  notice.after(help);
  function actions(g){
    if(!valid(g))return '';
    const ctx=window.GamesSteamContext?.()||{owned:new Set(),wishlist:new Set()},id=g.appid;
    const label=ctx.owned.has(id)?'View on Steam':ctx.wishlist.has(id)?'Manage wishlist on Steam':'Wishlist on Steam';
    return `<div class="steam-wishlist-controls"><a class="quiet" data-steam-store-wishlist="${id}" href="https://store.steampowered.com/app/${id}/" target="_blank" rel="noopener noreferrer" title="Complete the action on Steam">${label} ${icon('external')}</a><a class="quiet steam-client-link" href="steam://store/${id}">Open in Steam</a></div>`;
  }
  card=function(g){return previous.card(g).replace('<div class="card-body">','<div class="card-body">'+actions(g));};
  table=function(){const t=document.createElement('template');t.innerHTML=previous.table();for(const row of t.content.querySelectorAll('tbody tr')){const g=byId.get(row.querySelector('[data-open]')?.dataset.open);if(g)row.querySelector('td')?.insertAdjacentHTML('beforeend',actions(g));}return t.innerHTML;};
  sourcePanel=function(g){return previous.source(g)+`<section class="detail-section steam-wishlist-section"><h3>Steam actions</h3>${actions(g)||'<p>No exact Steam AppID is attached to this entry. No Steam action is inferred.</p>'}<p>Complete wishlist additions or removals on Steam, then refresh this snapshot. Local favorites and Want to play remain separate.</p></section>`;};
  document.addEventListener('click',event=>{
    if(!event.target.closest('[data-steam-store-wishlist]'))return;
    notice.textContent='Opening the official Steam page. Complete wishlisting there, then refresh or import your snapshot. No Steam change is assumed.';notice.hidden=false;
  });
  render();
})();
