/* Official Steam handoff and consent-loaded Valve widget. No account-write API. */
'use strict';
(function installSteamWishlistActions(){
  const previous={card,table,source:sourcePanel,render};
  let membership={owned:new Set(),wishlist:new Set()};
  // Copy the account sets once per render, never once for every game card.
  render=function(){membership=window.GamesSteamContext?.()||{owned:new Set(),wishlist:new Set()};return previous.render();};
  const valid=g=>typeof g?.appid==='number'&&Number.isSafeInteger(g.appid)&&g.appid>0&&g.appid<=4294967295;
  const notice=document.createElement('p');notice.className='steam-action-feedback';notice.setAttribute('role','status');notice.setAttribute('aria-live','polite');notice.hidden=true;
  $('.steam-library-strip').after(notice);
  const help=document.createElement('details');help.className='steam-wishlist-help';
  help.innerHTML='<summary>How Steam wishlist actions work</summary><p>Wishlist on Steam opens the exact official app page. Add or remove the game there using Steam\'s own controls, then refresh your snapshot here. A click on this site does not claim that Steam changed your wishlist.</p><p>Game details also offer Valve\'s official widget, loaded only when you choose. Steam supplies an Add to Wishlist button for unreleased games and purchase controls for released games. Browser privacy settings or Steam sign-in may require completing the action on Steam.</p><p>Steam sign-in verifies identity; it does not grant wishlist-write permission. This site does not read Steam cookies, ask for passwords or API keys, or send undocumented account-changing requests.</p>';
  notice.after(help);
  function actions(g){
    if(!valid(g))return '';
    const ctx=membership,id=g.appid;
    const label=ctx.owned.has(id)?'View on Steam':ctx.wishlist.has(id)?'Manage wishlist on Steam':'Wishlist on Steam';
    return `<div class="steam-wishlist-controls"><a class="quiet" data-steam-store-wishlist="${id}" href="https://store.steampowered.com/app/${id}/" target="_blank" rel="noopener noreferrer" title="Complete the action on Steam">${label} ${icon('external')}</a><a class="quiet steam-client-link" href="steam://store/${id}">Open in Steam</a></div>`;
  }
  function widget(g){
    if(!valid(g))return '';
    return `<div class="steam-widget-slot" data-steam-widget-slot="${g.appid}" style="max-width:100%;overflow:hidden"><button class="secondary" data-steam-widget="${g.appid}">Load Valve's Steam widget</button><p>Optional third-party content: loading contacts Steam. For unreleased games, Valve supplies an Add to Wishlist button; released games show purchase controls. Your local snapshot is updated only by a later sync/import, never by assuming a widget click succeeded.</p></div>`;
  }
  card=function(g){return previous.card(g).replace('<div class="card-body">','<div class="card-body">'+actions(g));};
  table=function(){const t=document.createElement('template');t.innerHTML=previous.table();for(const row of t.content.querySelectorAll('tbody tr')){const g=byId.get(row.querySelector('[data-open]')?.dataset.open);if(g)row.querySelector('td')?.insertAdjacentHTML('beforeend',actions(g));}return t.innerHTML;};
  sourcePanel=function(g){return previous.source(g)+`<section class="detail-section steam-wishlist-section"><h3>Steam actions</h3>${actions(g)||'<p>No exact Steam AppID is attached to this entry. No Steam action is inferred.</p>'}<p>Complete wishlist additions or removals on Steam, then refresh this snapshot. Local favorites and Want to play remain separate.</p>${widget(g)}</section>`;};
  document.addEventListener('click',event=>{
    const load=event.target.closest('[data-steam-widget]');
    if(load){
      const id=Number(load.dataset.steamWidget),g=games.find(x=>x.appid===id);
      if(!valid(g)||!event.isTrusted)return;
      const slot=load.closest('.steam-widget-slot');if(!slot||slot.querySelector('iframe'))return;
      const frame=document.createElement('iframe');
      frame.title=`Official Steam widget for ${g.name}`;
      frame.src=`https://store.steampowered.com/widget/${id}/?l=english`;
      frame.referrerPolicy='no-referrer';frame.loading='lazy';frame.width='100%';frame.height='230';
      frame.style.cssText='display:block;width:100%;max-width:100%;border:0;margin:12px 0';
      frame.setAttribute('sandbox','allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox allow-top-navigation-by-user-activation');
      load.disabled=true;load.textContent='Steam widget requested';slot.prepend(frame);
      return;
    }
    if(!event.target.closest('[data-steam-store-wishlist]'))return;
    notice.textContent='Opening the official Steam page. Complete wishlisting there, then refresh or import your snapshot. No Steam change is assumed.';notice.hidden=false;
  });
  render();
})();
