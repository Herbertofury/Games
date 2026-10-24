"""Document source-matched party coverage without inventing runtime success."""
from collections import Counter
import datetime as dt,json,pathlib
R=pathlib.Path(__file__).resolve().parents[1];c=json.loads((R/'data/catalog.json').read_text());rows=[g for g in c['items'] if 'Couch co-op & party' in g.get('hubs',[])];raw=json.loads((R/'data/party-reconciliation.json').read_text())
report={'checkedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'records':len(c['items']),'partyRecords':len(rows),'collections':len({g['partyCollection'] for g in rows}),'statuses':dict(Counter(g['status'] for g in rows)),'sourceReferences':sum(len(g['storefronts']) for g in rows),'providers':dict(Counter(s['provider'] for g in rows for s in g['storefronts'])),'knownCountRecords':sum(g['partyInfo']['countVerified'] for g in rows),'unconfirmedCountRecords':[{'id':g['id'],'name':g['name']} for g in rows if not g['partyInfo']['countVerified']],'unconfirmedModeCount':len(raw.get('unresolved',[])),'participation':dict(Counter(g['partyInfo']['participation'] for g in rows)),'byExactCount':{str(n):sum(n in g['partyInfo']['playerCounts'] for g in rows) for n in range(2,9)},'artwork':sum(bool(g.get('image')) for g in rows),'video':sum(bool(g.get('trailers')) for g in rows),'notPromoted':raw.get('dispositions',[]),'datasetHash':c['build']['datasetHash']}
(R/'data/party-study-report.json').write_text(json.dumps(report,indent=2)+'\n')
body=f'''# Games: one more round

The couch co-op and party hub contains {len(rows)} unique entries in {report['collections']} collections, in the shared library of {len(c['items'])} records. All previous 1,567 identities and seven earlier genre memberships are preserved. Cross-genre games are not counted twice globally.

The collection is centered on Disc Jam, Lethal League and Blaze, Thunder Rally, Hyper Jam, and Boomerang Fu. Competitive arena knockouts, ricochet duels, sports, racing and bigger-couch chaos are distinguished from two-person adventures, cooperative campaigns, and phone-controlled parties.

The party lobby combines exact headcount, cooperative or competitive mode, simultaneous/phone/hotseat/asymmetric setup, PC/console edition and additional-DLC conditions. The selected count must fit the same selected mode. A four-player versus limit never becomes a four-player cooperative campaign. Bots, spectators, online limits and tournament brackets are not couch participants.

Every published entry has source-grounded artwork, supported embedded-video metadata and confirmed distribution links. Creator animation conversions and community footage retain their provenance. The native wiki renders artwork and links exact videos; the portable HTML provides in-page players.

{report['knownCountRecords']} entries have source-confirmed numerical local capacities. The {len(report['unconfirmedCountRecords'])} remaining entries have confirmed local support but visibly unconfirmed numerical limits, and are excluded from exact-number filters. Some games have one known mode and a separately unconfirmed secondary mode; their details retain that distinction. Unknown does not mean zero, or an invented four-player limit.

Mode-specific capacity is visible on cards, in tables, comparisons and full dossiers, and in CSV/JSON exports. Saved filters, personal ratings, notes, backlog and favorites retain games.library.v1. No scheduled crawler, synthesized artwork or viewport culling was introduced.

The publication gate retains every earlier source/unit and browser regression and adds exhaustive party dossier/source-button and primary-image checks, mode-intersection tests, real persistence, mobile layouts and actual selected video playback. Successful video probes are not a claim that every external video was watched end to end. Store coverage is the confirmed set, not every worldwide retailer.

Wiki pages: Couch-Coop-and-Party, Party-Media, Party-Player-Guide, Party-Two-Players, Party-Four-Players and Party-Five-Plus. GitHub Pages is a separate repository hosting prerequisite; native wiki and portable HTML do not depend on it.
'''
(R/'docs/RELEASE.md').write_text(body);(R/'docs/PARTY.md').write_text(body+'\n## Coverage snapshot\n\n```json\n'+json.dumps(report,indent=2)+'\n```\n\n## Maintaining the same collection\n\nThe party source snapshots, storefront discoveries, reviewed curation and media layers remain separate. Update only changed identities. Preserve `partyInfo.modesDetail` and its exact-edition evidence when refreshing Steam facts; Steam local-support categories do not provide numerical capacities. Run the party model/build, unit tests and party browser gate, then the standard full publication workflow. Unknown count modes remain in `data/party-reconciliation.json` until a source confirms them.\n')
print(json.dumps(report,indent=2))
