#!/usr/bin/env python3
"""Build a portable catalog, matching wiki, provenance manifest, and release archive."""
import argparse,csv,datetime as dt,hashlib,html,json,pathlib,re,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO='https://github.com/Herbertofury/Games'
SITE='https://herbertofury.github.io/Games/'
def slug(s): return re.sub(r'[^A-Za-z0-9]+','-',s).strip('-')
def md(s): return str(s or '').replace('|','\\|').replace('\n',' ').replace('<','&lt;').replace('>','&gt;')
def score(g):
    if g.get('verification')!='verified' or g.get('fit') is None:return None
    n=g['fit'];r=g.get('rating');count=g.get('reviewCount',0)
    if count<30:n=min(n,7)
    if r is not None and count>=30:
        if r<50:n=min(n,5)
        elif r<70:n=min(n,6)
        elif r<80:n=min(n,7)
    return n
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',default='data/catalog.json');args=ap.parse_args()
    path=ROOT/args.data;catalog=json.loads(path.read_text());games=catalog['items'];assert games,'Empty catalogs cannot be published'
    assert len({g['id'] for g in games})==len(games),'Duplicate IDs'
    assert all(re.match(r'^https://store\.steampowered\.com/app/\d+/$',g['steamUrl']) for g in games),'Invalid canonical Steam URL'
    out=ROOT/'dist';out.mkdir(exist_ok=True);wiki=ROOT/'wiki';wiki.mkdir(exist_ok=True);assets=out/'assets';assets.mkdir(exist_ok=True)
    def source(name):return (ROOT/'site'/name).read_text()
    data=json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    app=source('app.js').replace('</script','<\\/script')
    page=source('index.html').replace('/*__CSS__*/',source('styles.css')).replace('/*__DATA__*/','window.GAMES_CATALOG='+data+';').replace('/*__APP__*/',app)
    assert not any(x in page for x in ['/*__CSS__*/','/*__DATA__*/','/*__APP__*/'])
    (out/'index.html').write_text(page);(out/'.nojekyll').write_text('');shutil.copyfile(ROOT/'site/sw.js',out/'sw.js');shutil.copyfile(path,out/'catalog.json')
    verified=[g for g in games if g.get('verification')=='verified'];unresolved=[g for g in games if g.get('verification')!='verified'];collections=sorted({g['collection'] for g in games})
    trailer_count=sum(any(t.get('mp4') or t.get('webm') or t.get('hls') for t in g.get('trailers',[])) for g in games)
    banner=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="400" viewBox="0 0 1400 400"><defs><linearGradient id="a"><stop stop-color="#111b13"/><stop offset="1" stop-color="#2d4128"/></linearGradient><radialGradient id="b"><stop stop-color="#c2ed8b" stop-opacity=".13"/><stop offset="1" stop-color="#c2ed8b" stop-opacity="0"/></radialGradient></defs><rect width="1400" height="400" rx="22" fill="url(#a)"/><circle cx="1100" cy="180" r="400" fill="url(#b)"/><g fill="none" stroke="#c2ed8b" stroke-opacity=".13" transform="translate(1100 200) rotate(45)"><rect x="-140" y="-140" width="280" height="280" rx="24"/><rect x="-100" y="-100" width="200" height="200" rx="16"/><rect x="-60" y="-60" width="120" height="120" rx="8"/></g><text x="65" y="82" fill="#c2ed8b" font-family="Arial,sans-serif" font-size="17" letter-spacing="5">GAMES / THE PERSONAL COLLECTION</text><text x="60" y="191" fill="#f0f4e9" font-family="Arial,sans-serif" font-size="82" font-weight="bold" letter-spacing="-3">One more run.</text><text x="65" y="239" fill="#b8c6ad" font-family="Arial,sans-serif" font-size="21">The roguelite collection. Your next obsession starts here.</text><path d="M65 282h770" stroke="#809373" stroke-opacity=".3"/><text x="65" y="329" fill="#d1e5bc" font-family="Arial,sans-serif" font-size="18">{len(games)} GAMES   /   {len(collections)} COLLECTIONS   /   {trailer_count} WITH OFFICIAL TRAILERS</text></svg>'''
    (assets/'collection-banner.svg').write_text(banner)
    header=f'![Games: The Roguelite Collection]({REPO}/raw/main/dist/assets/collection-banner.svg)\n\n'
    jump=f'### [Open the interactive collection]({SITE})\n\n**Filters, sortable ratings, embedded trailers, comparison, favorites, notes, and personal play status live in the companion.** The wiki is the readable, versioned reference.\n\n'
    freshness=f"Steam snapshot: **{catalog.get('generatedAt','Unknown')}**. **{len(verified)} verified identities**, **{len(unresolved)} awaiting verification**. Prices are US snapshots, not live quotes.\n\n"
    home=header+'# A home for every great discovery\n\n'+jump+'Start with **[Roguelites](Roguelites)**: survivors-likes, dark fantasy, bullet heavens, active-combat roguelites, and a clearly separated shelf of adjacent loot-driven action RPGs.\n\n'+freshness+'| Explore | What is inside |\n|:--|:--|\n| [Roguelites](Roguelites) | Every recommendation from both discovery lists, deduplicated and rechecked. |\n| [Collections](Collections) | Theme and mechanic shelves, from dark fantasy to unusual hybrids. |\n| [How recommendations work](Ratings-and-Sources) | Steam ratings, review confidence, editorial fit, and provenance. |\n| [Add and update games](Updating-the-Library) | One canonical master list and a repeatable refresh pipeline. |\n| [Needs verification](Needs-Verification) | Preserved suggestions that still need official confirmation. |\n\n## Built to keep growing\n\nThe master source is [`data/seeds.tsv`]('+REPO+'/blob/main/data/seeds.tsv). Verified facts and media live in [`data/catalog.json`]('+REPO+'/blob/main/data/catalog.json). Both the interactive library and these wiki pages are generated from that same snapshot. New genres can join this home without splitting the source of truth.\n'
    (wiki/'Home.md').write_text(home)
    def game_link(g):return f'Game-{g["appid"]}-{slug(g["name"])}'
    def table(rows):
        s='| Game | Recommendation | Steam | Reviews | Release | Status |\n|:--|:--:|:--:|--:|:--|:--|\n'
        for g in rows:
            sc=score(g);s+=f"| [{md(g['name'])}]({game_link(g)}) | {str(sc)+'/10' if sc is not None else 'Pending'} | {str(g.get('rating'))+'%' if g.get('rating') is not None else 'Unknown'} | {g.get('reviewCount',0):,} | {md(g.get('releaseLabel'))} | {md(g.get('status'))} |\n"
        return s+'\n'
    rank=lambda g:(-(score(g) or -1),-(g.get('reviewCount') or 0),g['name'].lower())
    rog=header+'# Roguelites\n\n'+jump+freshness+'## Start here\n\nEditorial fit and Steam reception are deliberately separate. These picks have strong relevance and a meaningful player-review sample.\n\n'
    picks=sorted([g for g in verified if (score(g) or 0)>=9 and g.get('reviewCount',0)>=100 and not g.get('comingSoon')],key=rank)
    rog+=table(picks[:15])+'## Every recommendation, by collection\n\n'
    for c in collections:
        rows=sorted([g for g in games if g['collection']==c],key=rank);rog+='### '+c+'\n\n'+table(rows)
    rog+='## Score and date notes\n\n[Read the methodology](Ratings-and-Sources). Early Access start dates and full-release dates can differ. Unresolved records are visible, but do not receive invented ratings or recommendation scores. This is a curated discovery catalog, not a claim that every niche entry is a great purchase.\n'
    (wiki/'Roguelites.md').write_text(rog)
    cs=header+'# Collections\n\n'+jump
    for c in collections:
        cs+='## '+c+'\n\n'+table(sorted([g for g in games if g['collection']==c],key=rank))
    (wiki/'Collections.md').write_text(cs)
    for g in games:
        sc=score(g);s=f'# {md(g["name"])}\n\n'
        if g.get('image'):s+=f'![{md(g["name"])} official artwork]({g["image"]})\n\n'
        s+=f'**[Steam store]({g["steamUrl"]})** &nbsp; | &nbsp; **[Watch trailers / open interactive details]({SITE}#game={g["id"].replace(":","%3A")})** &nbsp; | &nbsp; [Back to Roguelites](Roguelites)\n\n'
        s+=f"{md(g.get('summary'))}\n\n| Field | Value |\n|:--|:--|\n| Collection | {md(g['collection'])} |\n| Recommendation | {str(sc)+'/10' if sc is not None else 'Pending verification'} |\n| Steam positive reviews | {str(g.get('rating'))+'%' if g.get('rating') is not None else 'Unknown'} |\n| Review count | {g.get('reviewCount',0):,} |\n| Steam release date | {md(g.get('releaseLabel'))} |\n| Status | {md(g.get('status'))} |\n| Developers | {md(', '.join(g.get('developers',[])))} |\n| US price snapshot | {'Free' if g.get('free') else md(g.get('price') or 'Unknown')} |\n| Last verified | {md(g.get('verifiedAt') or 'Not verified')} |\n\n"
        if g.get('warnings'):s+='> **Check before buying:** '+md('; '.join(g['warnings']))+'\n\n'
        s+='## Official media\n\n'
        for t in g.get('trailers',[]):
            url=t.get('mp4') or t.get('webm') or t.get('hls')
            if url:s+=f'- [{md(t.get("name") or "Official trailer")}]({url})\n'
        s+='\n'
        for image in g.get('screenshots',[]):s+=f'![{md(image.get("alt") or g["name"])}]({image["src"]})\n\n'
        s+='## Source and recommendation notes\n\nSteam facts and media are official store data. The recommendation is editorial fit, not a play-tested review. [Full scoring and source policy](Ratings-and-Sources). Personal favorites, notes, and your own ratings are kept separately in the interactive library.\n'
        (wiki/(game_link(g)+'.md')).write_text(s)
    (wiki/'Ratings-and-Sources.md').write_text('''# Ratings, recommendations, and sources

## Three distinct scores

**Steam rating** is the positive percentage across all languages and all purchase types, with the full review count beside it. This can differ from the localized Steam store headline. Small samples are flagged.

**Recommendation** is editorial relevance to the requested style, on a 1 to 10 scale. It is not a claim of hands-on testing. Start here: 9 to 10. Strong picks: 8. Explore: 7. Deep cuts: 6 or below. A verified game's initial fit is set in the seed file. Fewer than 30 reviews cap the score at 7. With at least 30 reviews, under 50% positive caps it at 5, under 70% at 6, and under 80% at 7. Unverified identities receive no score. Upcoming games are watchlist entries.

**Your personal rating** is your own score after playing, stored privately in your browser alongside notes and play status. It never overwrites Steam reception or the editorial recommendation.

## Provenance

The two earlier recommendation lists are discovery inputs, not evidence. Current identity, availability, date, price, developers, screenshots and trailers are fetched from Steam's store API. Review totals come from Steam's review API. Every verified entry carries its source URLs and timestamp. Ambiguous identity matches are held for verification. No invented dates, scores, screenshots, or trailer IDs are inserted.

Steam's store release date can reflect full release rather than the first Early Access launch. Prices are US-store snapshots and must be rechecked before purchase. A removed or inaccessible listing is not silently deleted. Refresh failures retain the previous verified snapshot, original verification timestamp, and a warning.

## Media and offline use

Official developer artwork and trailers are served by Steam. Native MP4/WebM video is preferred; HLS.js 1.7.3 handles official HLS streams in compatible browsers. A blocked or absent stream retains an obvious Steam fallback. Screenshots have full-image viewing, thumbnails, and keyboard navigation.

The standalone HTML keeps the entire searchable catalog offline. Remote images, fonts and video require a connection unless already cached. No account, API key, analytics, or advertising is required.

## One source of truth

`data/seeds.tsv` owns the selection, collection and initial editorial fit. `data/catalog.json` owns the verified snapshot. The website and wiki are generated together. Personal browser data is independent; export a backup to transfer it between devices.
''')
    (wiki/'Needs-Verification.md').write_text('# Needs verification\n\nAll suggestions are retained. These entries are not yet endorsed as verified games.\n\n'+table(unresolved)+''.join(f"### {md(g['name'])}\n\n{md('; '.join(g.get('warnings',[])))}\n\n" for g in unresolved))
    (wiki/'_Sidebar.md').write_text(f'## GAMES\n\n[Open interactive library]({SITE})\n\n- [Home](Home)\n- [Roguelites](Roguelites)\n- [Collections](Collections)\n- [Ratings and sources](Ratings-and-Sources)\n- [Add / update games](Updating-the-Library)\n- [Needs verification](Needs-Verification)\n\n---\n\n[Source repository]({REPO})\n')
    (wiki/'_Footer.md').write_text('**GAMES** · A living collection, not another forgotten list. · [Steam facts and scoring](Ratings-and-Sources)\n')
    guide=(ROOT/'docs/UPDATING.md')
    if guide.exists():shutil.copyfile(guide,wiki/'Updating-the-Library.md')
    manifest={'schemaVersion':1,'version':'1.0.0','builtAt':dt.datetime.now(dt.timezone.utc).isoformat(),'sourceRepository':REPO,'sourceRevision':__import__('os').environ.get('GITHUB_SHA'),'sourceWiki':REPO+'/wiki','datasetHash':catalog.get('build',{}).get('datasetHash'),'records':len(games),'verified':len(verified),'unresolved':len(unresolved),'trailers':trailer_count,'collections':collections,'html':{'bytes':(out/'index.html').stat().st_size,'sha256':digest(out/'index.html')},'sourceFiles':{str(p.relative_to(ROOT)):digest(p) for d in ['site','scripts','tests','data'] for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.png','.jpg']}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    release=ROOT/'release';release.mkdir(exist_ok=True);shutil.copyfile(out/'index.html',release/'Games - Explorer.html')
    with zipfile.ZipFile(release/'Games - Library.zip','w',zipfile.ZIP_DEFLATED,9) as z:
        for folder in ['site','scripts','data','wiki','dist','docs','tests','.github']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.png','.jpg']:z.write(p,str(p.relative_to(ROOT)))
        for name in ['README.md','LICENSE','requirements-dev.txt']:
            if (ROOT/name).exists():z.write(ROOT/name,name)
    (release/'SHA256SUMS.txt').write_text('\n'.join(f'{digest(p)}  {p.name}  {p.stat().st_size} bytes' for p in release.iterdir() if p.name!='SHA256SUMS.txt')+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='sourceFiles'},indent=2))
if __name__=='__main__':main()
