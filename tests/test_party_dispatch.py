import pathlib,re,subprocess,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class PartyDispatchTests(unittest.TestCase):
 def test_comparison_action_uses_current_hub_renderer(self):
  source=(R/'site/app.js').read_text()
  handler=re.search(r",compare:(.*?),'clear-compare':",source).group(1)
  js='let calls=[];let openCompare=()=>calls.push("base");const actions={compare:'+handler+'};openCompare=()=>calls.push("party");actions.compare();if(calls.join()!=="party")throw new Error("Stale comparison action");'
  subprocess.run(['node','-e',js],check=True)
if __name__=='__main__':unittest.main()
