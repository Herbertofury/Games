import pathlib,re,subprocess,unittest
R=pathlib.Path(__file__).resolve().parents[1]
class ArcadePauseTests(unittest.TestCase):
 def test_footer_label_survives_overlay_pause_button(self):
  source=(R/'site/arcade.js').read_text()
  pause=re.search(r' function pause\(\)\{.*?(?=\n function open\()',source,re.S).group(0)
  harness=r"""
let running=true,paused=false,overlayExists=false;
const footer={textContent:'Pause'},overlayButton={textContent:'Back to the nonsense'};
const overlay={hidden:true,set innerHTML(value){overlayExists=value.includes('data-arcade="pause"');}};
function $(selector){
 if(selector==='#arcade-overlay')return overlay;
 if(selector==='.arcade-footer [data-arcade="pause"]')return footer;
 if(selector==='[data-arcade="pause"]')return overlayExists?overlayButton:footer;
 throw Error('Unexpected selector '+selector);
}
const cv={focus(){}};
function refresh(){}
__PAUSE__
pause();if(!paused||footer.textContent!=='Resume'||overlay.hidden)throw Error('Pause state mismatch');
pause();if(paused||footer.textContent!=='Pause'||!overlay.hidden)throw Error('Resume footer mismatch');
pause();if(!paused||footer.textContent!=='Resume'||overlay.hidden)throw Error('Repeated pause mismatch');
pause();if(paused||footer.textContent!=='Pause'||!overlay.hidden)throw Error('Repeated resume mismatch');
"""
  result=subprocess.run(['node','-e',harness.replace('__PAUSE__',pause)],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr)
  broken=pause.replace('.arcade-footer [data-arcade="pause"]','[data-arcade="pause"]')
  bad=subprocess.run(['node','-e',harness.replace('__PAUSE__',broken)],capture_output=True,text=True)
  self.assertNotEqual(bad.returncode,0,'Known ambiguous selector must fail this regression')
  self.assertIn('Resume footer mismatch',bad.stderr)
if __name__=='__main__':unittest.main()
