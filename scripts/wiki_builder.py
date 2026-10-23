"""Provider-aware native wiki, generated from the same snapshot as the interactive app."""
import html,json,pathlib,urllib.parse
from catalog_model import score,primary,game_key
REPO='https://github.com/Herbertofury/Games';SITE='https://herbertofury.github.io/Games/'
def m(v):return str(v or '').replace('|','\\|').replace('\n',' ').replace('<','&lt;').replace('>','&gt;')
def link(filters):return SITE+'#'+urllib.parse.urlencode(filters)
def rating(g):
    if g.get('rating') is not None:return f"{g['rating']}% / {g.get('reviewCount',0):,} Steam reviews"
    r=g.get('externalRating');return f"{r['value']}/{r['max']} / {r['count']} {r['provider']} ratings" if r else 'No aggregate rating'
def rank(g):return (-(score(g) or -1),-g.get('reviewCount',0),g['name'].casefold())
def table(rows):
    out='| Game | Recommend | Community reception | Release / build | Where |\n|:--|:--:|:--|:--|:--|\n'
    for g in rows:
        places=' · '.join(f"[{m(x['provider'])}]({x['url']})" for x in g.get('storefronts',[]) if x.get('kind')!='support')
        out+=f"| [{m(g['name'])}]({game_key(g)}) | {str(score(g))+'/10' if score(g) is not None else 'Unrated'} | {m(rating(g))} | {m(g.get('releaseLabel','Unknown'))} · {m(g.get('status'))} | {places} |\n"
    return out+'\n'
def build_wiki(root,catalog):
    games=catalog['items'];out=root/'wiki';out.mkdir(exist_ok=True);assets=root/'dist/assets';assets.mkdir(exist_ok=True)
    hubs={'Roguelites':[g for g in games if 'Roguelites' in g.get('hubs',[])],'Boomer shooters':[g for g in games if 'Boomer shooters' in g.get('hubs',[])]}
    for hub,title,sub,color,file in [('Roguelites','One more run.','Ridiculous builds. Impossible odds. Endless discoveries.','#c2ed8b','collection-banner.svg'),('Boomer shooters','Make some noise.','New releases. Hidden gems. The underground FPS scene.','#f6b66a','shooters-banner.svg')]:
        rows=hubs[hub]
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="390" viewBox="0 0 1400 390"><defs><linearGradient id="b"><stop stop-color="#141712"/><stop offset="1" stop-color="#2b2119"/></linearGradient></defs><rect width="1400" height="390" rx="20" fill="url(#b)"/><g fill="none" stroke="{color}" stroke-opacity=".15"><circle cx="1190" cy="190" r="140"/><circle cx="1190" cy="190" r="100"/><path d="M970 190h440M1190 0v390"/></g><text x="64" y="75" font-family="Arial,sans-serif" font-size="16" letter-spacing="5" fill="{color}">GAMES / THE PERSONAL COLLECTION</text><text x="60" y="187" font-family="Arial,sans-serif" font-size="80" font-weight="bold" fill="#f3f2ec">{title}</text><text x="65" y="239" font-family="Arial,sans-serif" font-size="21" fill="#b8b6ad">{sub}</text><path d="M65 280h800" stroke="{color}" opacity=".2"/><text x="65" y="327" font-family="Arial,sans-serif" font-size="17" fill="{color}">{len(rows)} DISCOVERIES / OFFICIAL MEDIA / YOUR NEXT OBSESSION</text></svg>'''
        (assets/file).write_text(svg)
    def head(hub):
        return f"![{hub} collection]({REPO}/raw/main/dist/assets/{'shooters-banner.svg' if hub=='Boomer shooters' else 'collection-banner.svg'})\n\n"
    def intro(hub):return head(hub)+f"# {hub}\n\n### [Open the interactive {hub.lower()} library]({link({'hub':hub})})\n\n**Search, filters, sortable ratings, embedded trailers, full galleries, favorites, private notes, and comparison.** All records below use the same source snapshot as the app.\n\n"
    def cards(rows):
        text='<table>\n'
        for i in range(0,len(rows),3):
            text+='<tr>\n'
            for g in rows[i:i+3]:
                text+='<td width="33%" valign="top">\n\n'
                if g.get('image'):text+=f"[![{m(g['name'])}]({g['image']})]({game_key(g)})\n\n"
                text+=f"**[{m(g['name'])}]({game_key(g)})**\n\n{score(g)}/10 recommendation · {m(g.get('status'))}\n\n{m(g.get('curatorWhy') or g.get('summary'))}\n\n[Official page]({primary(g)}) · [Trailers & gallery]({link({'game':g['id']})})\n\n</td>\n"
            text+='</tr>\n'
        return text+'</table>\n\n'
    rog=hubs['Roguelites'];shoot=hubs['Boomer shooters'];total=len(games)
    home=head('Boomer shooters')+'# A home for every great discovery\n\n'+f"**[Open your interactive library]({SITE})** · [Roguelites](Roguelites) · [Boomer shooters](Boomer-Shooters) · [Beyond Steam](Beyond-Steam) · [Creator support](Creator-Support)\n\n"
    home+=f"**{total} unique recommendations.** {len(rog)} in Roguelites; {len(shoot)} in Boomer shooters. Cross-genre games appear in both hubs but exist only once in the master catalog.\n\n"
    home+='| Start exploring | What you will find |\n|:--|:--|\n| [Boomer shooters](Boomer-Shooters) | Recent launches, fast movement, occult campaigns, free standalone games, and mod-scene discoveries. |\n| [Roguelites](Roguelites) | Every original recommendation, with your Halls of Torment collection preserved. |\n| [Beyond Steam](Beyond-Steam) | itch.io, GOG, ModDB, creator sites, browser games, and explicit install requirements. |\n| [Creator support](Creator-Support) | Verified Patreon support links, kept separate from game purchase and download links. |\n| [Collections](Collections) | Every theme and subgenre. |\n| [Ratings and sources](Ratings-and-Sources) | Editorial recommendation versus platform reviews. |\n| [Add / update games](Updating-the-Library) | One repeatable pipeline, no disconnected lists. |\n'
    (out/'Home.md').write_text(home)
    for hub,rows,filename in [('Roguelites',rog,'Roguelites.md'),('Boomer shooters',shoot,'Boomer-Shooters.md')]:
        text=intro(hub)
        text+=f"**{len(rows)} unique entries** · [Playable now]({link({'hub':hub,'playable':'true'})}) · [Newest releases]({link({'hub':hub,'playable':'true','sort':'newest'})}) · [Hidden gems]({link({'hub':hub,'hidden':'true'})}) · [Beyond Steam]({link({'hub':hub,'offSteam':'true'})})\n\n"
        text+='Full releases, Early Access, demos, prototypes, mods, and future releases are labelled separately. Recent patches do not replace original launch dates. Recommendations are researched editorial judgments, not claims of hands-on testing.\n\n'
        picks=sorted([g for g in rows if (score(g) or 0)>=9 and g.get('status') in ['Released','Early Access']],key=rank)
        if hub=='Boomer shooters':
            focus=['steam:3115160','steam:2680280','steam:3748520','steam:2881610','steam:1592280','steam:2443360','external:qbj3','external:ashes-2063','steam:3808730']
            lookup={g['id']:g for g in rows};picks=[lookup[i] for i in focus if i in lookup]
        text+='## Start here\n\n'+cards(picks[:9])
        if hub=='Boomer shooters':
            recent=sorted([g for g in rows if (g.get('releaseDate') or '').startswith('2026') and not g.get('comingSoon')],key=lambda g:g.get('releaseDate',''),reverse=True)
            text+='## New in 2026\n\n'+table(recent)
            gems=[g for g in rows if g.get('hiddenGem') or (10<=g.get('reviewCount',0)<=1500 and (g.get('rating') or 0)>=80 and not g.get('comingSoon'))]
            text+='## Under the radar\n\nSmaller-audience discoveries, not a claim that obscurity guarantees quality. Native platform rating scales remain separate.\n\n'+table(sorted(gems,key=rank))
            ext=[g for g in rows if not g.get('steamUrl')]
            text+='## Beyond the storefronts\n\nStandalone releases and mods have different requirements. Open a game page before downloading; free mod files can still require an owned base game.\n\n'+table(sorted(ext,key=rank))
            future=[g for g in rows if g.get('comingSoon') or g['status'] in ['Demo','Prototype']]
            text+='## Demos, prototypes, and the watchlist\n\nA playable demo is not a released full game. Support subscriptions are not automatic game licenses.\n\n'+table(sorted(future,key=rank))
        text+='## The complete collection\n\n'
        for col in sorted({c for g in rows for c in g.get('collections',[g['collection']])}):
            text+='### '+col+'\n\n'+table(sorted([g for g in rows if col in g.get('collections',[g['collection']])],key=rank))
        text+='[Ratings and source methodology](Ratings-and-Sources) · [Update this library](Updating-the-Library)\n'
        (out/filename).write_text(text)
    cols='# Collections\n\nEvery genre shares one canonical library.\n\n'
    for c in sorted({c for g in games for c in g.get('collections',[g['collection']])}):cols+='## '+c+'\n\n'+table(sorted([g for g in games if c in g.get('collections',[g['collection']])],key=rank))
    (out/'Collections.md').write_text(cols)
    beyond='# Beyond Steam\n\n[Browse with platform filters]('+link({'offSteam':'true'})+')\n\nAlternate stores do not create duplicate game entries. Creator support is listed separately from buying or downloading a playable build.\n\n'
    providers=sorted({x['provider'] for g in games for x in g.get('storefronts',[]) if x['provider']!='Steam' and x.get('kind')!='support'})
    for provider in providers:beyond+='## '+provider+'\n\n'+table(sorted([g for g in games if any(x['provider']==provider and x.get('kind')!='support' for x in g.get('storefronts',[]))],key=rank))
    (out/'Beyond-Steam.md').write_text(beyond)
    supporters=[g for g in games if any(x.get('kind')=='support' for x in g.get('storefronts',[]))]
    support='# Creator support and Patreon\n\n**A support link is not a game license.** Public builds, demos, paid releases, and membership benefits are distinct. The library does not claim to have inspected member-only posts or verified private downloads. Read current creator tier descriptions before subscribing.\n\n'
    for g in sorted(supporters,key=rank):
        support+='## '+m(g['name'])+'\n\n'+m(g.get('curatorWhy') or g.get('summary'))+'\n\n'
        support+=' · '.join(f"[{m(x['provider'])} {'support / devlogs' if x.get('kind')=='support' else x.get('kind','page')}]({x['url']})" for x in g['storefronts'])+'\n\n'
    (out/'Creator-Support.md').write_text(support)
    for g in games:
        s=f"# {m(g['name'])}\n\n"
        if g.get('image'):s+=f"![{m(g['name'])} official artwork]({g['image']})\n\n"
        s+=f"**[Open official page]({primary(g)})** · **[Watch trailers and open gallery]({link({'game':g['id']})})** · "+' · '.join('[Boomer shooters](Boomer-Shooters)' if h=='Boomer shooters' else '[Roguelites](Roguelites)' for h in g.get('hubs',[]))+'\n\n'
        s+=m(g.get('summary'))+'\n\n'
        if g.get('curatorWhy'):s+='## Why it is here\n\n'+m(g['curatorWhy'])+'\n\n'
        s+='| Field | Value |\n|:--|:--|\n'
        fields={'Collection':', '.join(g.get('collections',[g['collection']])),'Recommendation':str(score(g))+'/10' if score(g) is not None else 'Unrated','Community reception':rating(g),'Release':g.get('releaseLabel') or 'Unknown','Availability':g.get('status'),'Build type':g.get('kind'),'FPS style':g.get('genreScope'),'Creators':', '.join(g.get('developers',[])),'Price snapshot':'Free / optional donation' if g.get('free') else g.get('price') or 'See official source','Verified':g.get('verifiedAt')}
        for k,v in fields.items():
            if v:s+=f'| {k} | {m(v)} |\n'
        s+='\n## Official stores and downloads\n\n'
        for x in g.get('storefronts',[]):s+=f"- [{m(x['provider'])}: {m(x.get('kind','official page'))}]({x['url']})\n"
        if g.get('requirements'):s+='\n### Before you play\n\n'+m(g['requirements'])+'\n'
        if g.get('updateNote'):s+='\n### Latest verified update\n\n'+m(g['updateNote'])+'\n'
        if g.get('warnings'):s+='\n> '+m('; '.join(g['warnings']))+'\n'
        s+='\n## Official media\n\nThe interactive library plays compatible trailers in-page. GitHub wiki links open their official source.\n\n'
        for t in g.get('trailers',[]):
            u='https://www.youtube.com/watch?v='+t['youtube'] if t.get('youtube') else t.get('mp4') or t.get('webm') or t.get('hls') or t.get('sourceUrl')
            if u:s+=f"[{m(t.get('name','Official trailer'))}]({u})\n\n"
        for im in g.get('screenshots',[]):s+=f"![{m(im.get('alt') or g['name'])}]({im['src']})\n\n"
        s+='## Sources and evidence\n\n'
        for x in g.get('sources',[]):s+=f"- [{m(x.get('label') or x.get('provider') or 'Source')}]({x['url']}) · checked {m(x.get('lastChecked',g.get('verifiedAt')))}\n"
        s+='\n[Score methodology](Ratings-and-Sources). Editorial recommendation is not a claim of hands-on testing.\n'
        (out/(game_key(g)+'.md')).write_text(s)
    (out/'Ratings-and-Sources.md').write_text('''# Ratings, sources, and recommendation confidence

Three scores stay separate: **Steam positive percentage**, **editorial recommendation /10**, and **your private personal rating**. itch.io and ModDB scores retain their native scale and sample size. They are never converted to a fabricated Steam percentage. Steam review filters apply only to Steam-scored entries.

For Steam, fewer than 30 reviews caps editorial recommendation at 7. At least 30 reviews with under 50%, 70%, or 80% positive cap it at 5, 6, or 7 respectively. For non-Steam releases, creator verification and documented community reception inform editorial fit; exploratory entries are capped at 7. No identity verification means no recommendation score.

Hidden gems: curated off-Steam discoveries or released Steam games with 10-1,500 reviews and at least 80% positive. This is a discovery filter, not a guarantee of quality. Core retro/movement shooters, tactical/immersive hybrids, melee-led games, and arena/roguelite FPS are labelled, not conflated.

Release dates mean the date supplied by the named source. Updates have separate notes. An unknown day stays unknown, and an updated mod is not labelled a newly launched game. A demo, prototype, paid game and standalone conversion are distinct. Mod downloads can require an owned base game. Patreon support does not automatically include playable builds or a game license.

The selection and curation are versioned in the repository. Official Steam snapshots, exact creator pages, documented download releases and linked media provide provenance. Screenshots and trailer IDs are not invented. Missing media remains missing with an official-source fallback. This is researched curation, not a claim of personally playing every game.

The complete catalog works offline. Uncached remote images and videos require internet. Favorites, notes, ratings and saved views stay in your browser, with export/import for transfer. No analytics, paid API key, or account is required. No scheduled scraping is enabled.
''')
    pending=catalog.get('build',{}).get('candidateUnresolved',[])
    (out/'Needs-Verification.md').write_text('# Discovery reconciliation\n\n'+f"Published catalog: {len(games)} unique records. Unresolved new candidates: {len(pending)}. Unresolved does not mean nonexistent.\n\n"+'\n'.join(f"- **{m(x.get('candidate'))}**: {m(x.get('error'))}" for x in pending)+'\n')
    (out/'_Sidebar.md').write_text(f'## GAMES\n\n[Open interactive library]({SITE})\n\n- [Home](Home)\n- [Boomer shooters](Boomer-Shooters)\n- [Roguelites](Roguelites)\n- [Beyond Steam](Beyond-Steam)\n- [Creator support](Creator-Support)\n- [Collections](Collections)\n- [Ratings and sources](Ratings-and-Sources)\n- [Add / update games](Updating-the-Library)\n- [Discovery reconciliation](Needs-Verification)\n\n[Source repository]({REPO})\n')
    (out/'_Footer.md').write_text('**GAMES** · A living collection, not another forgotten list. · [Sources and scoring](Ratings-and-Sources)\n')
    guide=root/'docs/UPDATING.md'
    if guide.exists():(out/'Updating-the-Library.md').write_text(guide.read_text())
