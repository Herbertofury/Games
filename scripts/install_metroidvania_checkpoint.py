"""Compose this genre addition with the current repository, never a stale snapshot."""
import importlib,json,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from catalog_model import assemble
# Include the freshly merged platformer source as well as the original 448 records.
before=assemble(json.loads((R/'data/catalog.json').read_text()));protected={'ids':sorted(g['id'] for g in before['items'] if any(h!='Metroidvanias' for h in g.get('hubs',[]))),'hubCounts':{h:n for h,n in before['build']['hubCounts'].items() if h!='Metroidvanias'}}
(R/'data/metroidvania-protected.json').write_text(json.dumps(protected,indent=2)+'\n')
p=R/'scripts/install_metroidvania_ui.py';s=p.read_text()
# Another legitimate genre expansion may already have generalized the old 448-only assertion.
old='patch(\'tests/test_rts.py\','
lines=s.splitlines();s='\n'.join(line for line in lines if not line.startswith(old))+'\n';p.write_text(s)
subprocess.run([sys.executable,str(p)],check=True)
subprocess.run([sys.executable,str(R/'scripts/finalize_metroidvania_ui.py')],check=True)
# Preserve the number floor and every exact protected ID, not a now-invalid fixed total.
p=R/'tests/test_metroidvania.py';s=p.read_text().replace("self.assertEqual(len(old['ids']),448)","self.assertGreaterEqual(len(old['ids']),448)")
s=s.replace("for h,n in [('Roguelites',170),('Boomer shooters',150),('Real-time strategy',130)]:self.assertEqual(sum(h in g['hubs'] for g in self.catalog['items']),n)","for h,n in old['hubCounts'].items():self.assertEqual(sum(h in g['hubs'] for g in self.catalog['items']),n)");p.write_text(s)
p=R/'tests/test_rts.py';s=p.read_text();s=s.replace("self.assertEqual(len(self.data['items']),448)","self.assertGreaterEqual(len(self.data['items']),448)").replace("self.assertEqual(len({g['id'] for g in self.data['items']}),448)","self.assertEqual(len({g['id'] for g in self.data['items']}),len(self.data['items']))");p.write_text(s)
p=R/'scripts/metroidvania_model.py';s=p.read_text();s=s.replace("old['metroidvaniaInfo']=g['metroidvaniaInfo'];", "old['aliases']=list(dict.fromkeys(old.get('aliases',[])+g.get('aliases',[])));old['metroidvaniaInfo']=g['metroidvaniaInfo'];");s=s.replace("set(old.get('tags',[])+g['tags'])", "set(t for t in old.get('tags',[]) if t not in genre_tags)|set(g['tags'])");p.write_text(s)
p=R/'scripts/build.py';s=p.read_text().replace("or t.get('youtube') for t", "or t.get('youtube') or t.get('vimeo') for t");s=s.replace("['site','scripts','data','wiki','dist','docs','tests','.github']", "['site','scripts','data','wiki','dist','docs','tests','media','.github']");p.write_text(s)
p=R/'site/app.js';s=p.read_text().replace('EXPLORATION ATLAS / 04','EXPLORATION ATLAS / 05').replace('04 / THE METROIDVANIA COLLECTION','05 / THE METROIDVANIA COLLECTION');p.write_text(s)
p=R/'site/index.html';p.write_text(p.read_text().replace('EXPLORATION ATLAS / 04','EXPLORATION ATLAS / 05'))
print('Protected non-Metroidvania records:',len(protected['ids']),protected['hubCounts'])
