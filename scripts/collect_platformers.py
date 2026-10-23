#!/usr/bin/env python3
"""Collect the reviewed platformer discovery set without guessing game identities.

App IDs in the TSV are discovery hints, not proof. Only an exact normalized
name or an explicitly reviewed alias can be promoted. No soundtrack, DLC,
demo, fuzzy sequel match, or release-date inference is accepted.
"""
from __future__ import annotations
import argparse, concurrent.futures, csv, datetime as dt, hashlib, json, pathlib, re, threading, unicodedata, urllib.parse
import refresh as steam
ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = 'Platformers'
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
ALIASES = {
    'N++': ['N++ (NPLUSPLUS)'],
    'Flashback': ['Flashback Classic'],
    'DARQ: Complete Edition': ['DARQ'],
    'Oddworld: Soulstorm Enhanced Edition': ['Oddworld: Soulstorm Enhanced Edition', 'Oddworld: Soulstorm'],
    'Disney Illusion Island': ['Disney Illusion Island Starring Mickey & Friends'],
}
# Reviewed corrections to discovery transcription, not fuzzy identity overrides.
CORRECTIONS = {
    'ibb & obb': {'fit': '8', 'appid': '95400'},
    "New Super Lucky's Tale": {'appid': '1038300'},
}
GROUPS = {
    'Precision & mastery': ('Precision platformer', 'Movement accuracy, readable hazards, checkpoint rhythm and repeatable mastery.', 'Difficulty and repeated attempts are part of the appeal; check assist options separately.'),
    'Speed & expressive movement': ('Momentum and speedrunning', 'Routes, momentum and expressive movement rather than simply reaching the exit.', 'Speed, combat and input demands vary; these are not all gentle traditional platformers.'),
    '3D worlds & collectathons': ('3D exploration platformer', 'Traversal through readable three-dimensional spaces, secrets and optional collection.', 'Camera behaviour and completionist demands matter as much as raw level count.'),
    'Puzzles & cinematic journeys': ('Puzzle or cinematic platformer', 'Spatial reasoning, environmental storytelling and movement as a problem-solving tool.', 'Some entries emphasize puzzles or atmosphere over mechanically demanding jumping.'),
    'Exploration & Metroidvanias': ('Exploration platformer / adjacent Metroidvania', 'Ability-gated exploration, spatial memory and routes that change as the movement kit grows.', 'Combat-heavy, top-down and unusual traversal hybrids are identified in the study; not every entry is a pure jumping game.'),
    'Action & retro adventures': ('Action platformer', 'Authored stages, readable encounters and the interplay of movement with combat.', 'Run-and-gun and classic collections remain distinct from precision-only platformers; collections are one catalog record.'),
    'Roguelite platformers': ('Roguelite platformer', 'Procedural runs, execution under uncertainty and meaningful build or route decisions.', 'Run resets and persistent progression differ substantially; a long run is not a short checkpoint challenge.'),
    'Co-op & playful chaos': ('Cooperative or competitive platformer', 'Coordination, shared problem solving or deliberately competitive stage construction.', 'Verify local versus online modes and player requirements on the exact store edition.'),
    'Colorful & approachable': ('Colorful platform adventure', 'Characterful worlds and accessible entry routes without assuming that optional challenges are easy.', 'Colorful art is not an age rating or an accessibility guarantee.'),
}

def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value.replace('\u2122', '').replace('\u00ae', '').replace('\u00a9', '').casefold().replace('&', 'and'))
    return ''.join(c for c in value if c.isascii() and c.isalnum())

# Reviewed current-title aliases preserve stable app identities.
ALIASES.update({
    'Big Hops': ['Big Hops Together'],
    'Demon Turf': ['Demon Turf: Queens Edition'],
    'kuso': ['LOVE 2: kuso'],
    'Lone Fungus 2': ['Lone Fungus: Melody of Spores'],
    'Nikoderiko: The Magical World': ["Nikoderiko: The Magical World - Director's Cut", 'Nikoderiko: The Magical World \u2014 Director\u2019s Cut'],
})
# Avoid a burst of public store requests. Reviews use a separate host.
import time
_get_unthrottled = steam.get
_request_lock = threading.Lock()
_next_request = [0.0]
def polite_get(url):
    if urllib.parse.urlsplit(url).hostname == 'store.steampowered.com':
        with _request_lock:
            delay = max(0.0, _next_request[0] - time.monotonic())
            if delay: time.sleep(delay)
            _next_request[0] = time.monotonic() + 0.75
    return _get_unthrottled(url)
steam.get = polite_get

def accepted(seed, title):
    return norm(title) in {norm(n) for n in [seed['name']] + ALIASES.get(seed['name'], [])}

def load_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default

_details = steam.details
_cache = {}
_lock = threading.Lock()
def cached_details(aid):
    key = str(aid)
    with _lock:
        if key in _cache:
            return _cache[key]
    value = _details(aid)
    with _lock:
        _cache[key] = value
    return value
steam.details = cached_details

def identify(seed):
    evidence = []
    aid = int(seed.get('appid') or 0)
    if aid:
        d = cached_details(aid)
        if d and d.get('type') == 'game' and accepted(seed, d.get('name', '')):
            return aid, d, evidence
        evidence.append({'hintAppid': aid, 'returnedName': (d or {}).get('name'), 'decision': 'Rejected mismatched or unavailable discovery hint'})
    query = 'https://store.steampowered.com/api/storesearch/?' + urllib.parse.urlencode({'term': seed['name'], 'l': 'english', 'cc': 'us'})
    result = steam.get(query)
    candidates = [r for r in result.get('items', []) if accepted(seed, r.get('name', ''))]
    verified = []
    for candidate in candidates:
        data = cached_details(candidate['id'])
        if data and data.get('type') == 'game' and accepted(seed, data.get('name', '')):
            verified.append((int(candidate['id']), data))
    unique = {i: d for i, d in verified}
    if len(unique) != 1:
        raise ValueError('Exact identity unresolved or ambiguous; candidates=' + repr([(x.get('id'), x.get('name')) for x in result.get('items', [])[:8]]) + '; rejected hints=' + repr(evidence))
    aid, d = next(iter(unique.items()))
    evidence.append({'query': query, 'matchedAppid': aid, 'matchedName': d['name'], 'decision': 'Exact normalized title or reviewed alias'})
    return aid, d, evidence

def collect(seed, old, force):
    prior = old.get(seed['name'])
    try:
        if prior and not force and prior.get('verifiedAt'):
            age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(prior['verifiedAt'])
            if age.total_seconds() < 86400:
                return prior, None
        aid, details, evidence = identify(seed)
        # Identity is already checked. resolve receives the exact official name
        # and the cached exact app details, not the original discovery guess.
        row = {'appid': str(aid), 'name': details['name'], 'collection': seed['collection'], 'fit': seed['fit']}
        game = steam.resolve(row, {}, True)
        if game.get('verification') != 'verified' or game.get('appid') != aid:
            raise ValueError('Verified identity did not survive provider collection: ' + repr(game.get('warnings')))
        scope, reason, caution = GROUPS[seed['collection']]
        game.update(seedName=seed['name'], seedId=str(aid), hubs=[HUB], collections=[seed['collection']], primaryUrl=game['steamUrl'], provider='Steam', kind='Standalone game', genreScope=scope, curatorWhy=reason, recommendationCaution=caution, editorialFit=int(seed['fit']), hiddenGem=seed['gem']=='yes', confidence='Source-grounded editorial selection', discoveryEvidence=evidence, researchCheckedAt=NOW)
        game['summary'] = ' '.join(game.get('summary', '').split()[:24]) + (' ...' if len(game.get('summary','').split()) > 24 else '')
        game['tags'] = sorted(set(game.get('tags', []) + ['Platformer', scope] + (['Editorial gem candidate'] if seed['gem']=='yes' else [])))
        game['demoAppids'] = [int(x['appid']) for x in details.get('demos', []) if x.get('appid')]
        game['platformerInfo'] = {'focus': scope, 'studyLens': reason, 'reviewBasis': 'Official Steam review API; exact query and collection time are retained with the sources.', 'platformScope': 'PC operating systems from Steam only; absence here does not imply console exclusivity.', 'editionNote': 'This record describes the exact listed store edition; its store date need not be the original game release.'}
        available = bool(details.get('is_free') or details.get('price_overview')) and not game.get('comingSoon')
        game['availability'] = 'Available in the checked US Steam snapshot' if available else 'Upcoming; wishlist only' if game.get('comingSoon') else 'Store page verified; current US purchase availability not confirmed'
        game['storefronts'] = [{'provider': 'Steam', 'url': game['steamUrl'], 'kind': 'store' if available else 'project', 'verified': True, 'lastChecked': NOW, 'availabilityNote': game['availability']}]
        if game.get('website') and game['website'].startswith('https://'):
            # A link returned by Steam is not a separately audited purchase link.
            game['platformerInfo']['developerWebsiteFromSteam'] = game['website']
        if game.get('comingSoon'):
            game['fit'] = None
            game['recommendationCaution'] = 'Watchlist only, not a current purchase recommendation. Release labels are publisher plans, not proof of availability.'
            game['hiddenGem'] = False
        elif game.get('reviewError') or game.get('reviewCount', 0) < 30:
            game['confidence'] = 'Exploratory'
            game['recommendationCaution'] += ' The current review evidence is limited; do not mistake a tiny sample for established quality.'
        if not available and not game.get('comingSoon'):
            game['recommendationCaution'] += ' Current purchase availability was not confirmed; follow the exact official page rather than assuming it is on sale.'
        if not game.get('trailers'):
            game['warnings'] = list(dict.fromkeys(game.get('warnings', []) + ['No embeddable trailer returned by the official API; use the source page.']))
        return game, None
    except Exception as exc:
        error = {'candidate': seed['name'], 'collection': seed['collection'], 'state': 'unresolved-active', 'reason': str(exc), 'checkedAt': NOW}
        if prior:
            prior['warnings'] = list(dict.fromkeys(prior.get('warnings', []) + ['Platformer refresh failed; retained dated prior snapshot']))
            prior['lastRefreshError'] = str(exc)
            return prior, error
        return None, error

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--workers', type=int, default=3)
    args = ap.parse_args()
    path = ROOT / 'data/platformers-seeds.tsv'
    rows = list(csv.DictReader(path.open(encoding='utf-8'), delimiter='\t'))
    assert len({norm(r['name']) for r in rows}) == len(rows), 'Duplicate discovery titles'
    for row in rows:
        row.update(CORRECTIONS.get(row['name'], {}))
        assert row['collection'] in GROUPS, row
        assert 1 <= int(row['fit']) <= 10, row
    old_data = load_json(ROOT / 'data/platformers-steam.json', {'items': []})
    old = {r['seedName']: r for r in old_data['items']}
    games, unresolved = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        jobs = {pool.submit(collect, row, old, args.force): row for row in rows}
        for future in concurrent.futures.as_completed(jobs):
            g, error = future.result()
            if g:
                games.append(g)
                print('VERIFIED', g['name'], g['appid'], g['status'], flush=True)
            if error:
                unresolved.append(error)
                print('UNRESOLVED', error['candidate'], error['reason'], flush=True)
    assert len({g['id'] for g in games}) == len(games), 'Resolved candidates collide; reconcile editions before publication'
    games.sort(key=lambda g: g['name'].casefold())
    unresolved.sort(key=lambda g: g['candidate'].casefold())
    by_seed = {g['seedName']: g for g in games}
    for row in rows:
        if row['name'] in by_seed:
            row['appid'] = str(by_seed[row['name']]['appid'])
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['name','collection','fit','gem','appid'], delimiter='\t', lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    result = {'schemaVersion': 1, 'hub': HUB, 'generatedAt': NOW, 'scope': 'Broad curated discovery, not an exhaustive inventory or hands-on playtest.', 'items': games, 'unresolved': unresolved}
    target = ROOT / 'data/platformers-steam.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    report = {'checkedAt': NOW, 'candidates': len(rows), 'verified': len(games), 'unresolved': unresolved, 'released': sum(g['status']=='Released' for g in games), 'earlyAccess': sum(g['status']=='Early Access' for g in games), 'upcoming': sum(g.get('comingSoon',False) for g in games), 'withImages': sum(bool(g.get('image')) for g in games), 'withVideos': sum(bool(g.get('trailers')) for g in games), 'reviewErrors': [g['id'] for g in games if g.get('reviewError')], 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT / 'data/platformers-enrichment-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['unresolved','reviewErrors']}, indent=2))
    if len(games) < 200:
        raise SystemExit('Too little verified coverage for this study; source files retained for investigation, publication blocked.')
if __name__ == '__main__':
    main()
