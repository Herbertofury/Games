import importlib.util
import json
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('image_decode_qa', ROOT / 'scripts/image_decode_qa.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PageStub:
    def evaluate(self, code, payload):
        self.code, self.payload = code, payload
        return payload


class ImageDecodeConfigTests(unittest.TestCase):
    def test_exact_rows_and_bounded_defaults(self):
        page = PageStub()
        rows = [{'id': 'one', 'image': 'https://example.test/exact.gif'}]
        result = module.decode_primary_images(page, rows)
        self.assertEqual(result['rows'], rows)
        self.assertEqual(result['maxAttempts'], 3)
        self.assertEqual(result['concurrency'], 5)
        self.assertEqual(result['retryDelayMs'], 750)

    def test_invalid_bounds_are_rejected(self):
        for kwargs in [{'max_attempts': 0}, {'max_attempts': 4}, {'concurrency': 0},
                       {'concurrency': 9}, {'timeout_ms': 0}, {'retry_delay_ms': -1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                module.decode_primary_images(PageStub(), [], **kwargs)

    @unittest.skipUnless(shutil.which('node'), 'Node is required for the isolated transport fixture')
    def test_real_retry_function_with_deterministic_image_fixture(self):
        harness = r'''
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const decode = eval('(' + input.code + ')');
const calls = {};
const plan = {pass:['ok'], retry:['error','ok'], fail:['error','error','error'],
              timeout:['timeout','ok'], zero:['zero','zero','zero']};
global.Image = class {
  constructor(){this.naturalWidth=0;this.naturalHeight=0;}
  set src(url){
    calls[url]=(calls[url]||0)+1;
    const result=(plan[url]||['error'])[calls[url]-1]||'error';
    if(result==='timeout') return;
    setTimeout(()=>{
      if(result==='error'){if(this.onerror)this.onerror();}
      else {this.naturalWidth=result==='zero'?0:32;this.naturalHeight=16;if(this.onload)this.onload();}
    },0);
  }
};
(async()=>{
 const rows=['pass','retry','fail','timeout','zero'].map(id=>({id,image:id}));
 rows.push({id:'missing',image:''});
 const output=await decode({rows,timeoutMs:8,maxAttempts:3,concurrency:2,retryDelayMs:0});
 process.stdout.write(JSON.stringify({output,calls}));
})().catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-e', harness], input=json.dumps({'code': module.IMAGE_DECODE_JS}),
                                text=True, capture_output=True, timeout=10, check=True)
        data = json.loads(result.stdout)
        rows = {row['id']: row for row in data['output']}
        self.assertEqual([row['id'] for row in data['output']], ['pass', 'retry', 'fail', 'timeout', 'zero', 'missing'])
        self.assertTrue(rows['pass']['ok'])
        self.assertEqual(len(rows['pass']['attempts']), 1)
        self.assertTrue(rows['retry']['ok'])
        self.assertEqual(len(rows['retry']['attempts']), 2)
        self.assertTrue(rows['timeout']['ok'])
        self.assertEqual(rows['timeout']['attempts'][0]['error'], 'timeout')
        self.assertFalse(rows['fail']['ok'])
        self.assertEqual(len(rows['fail']['attempts']), 3)
        self.assertFalse(rows['zero']['ok'])
        self.assertEqual(rows['zero']['error'], 'zero-dimension')
        self.assertFalse(rows['missing']['ok'])
        self.assertEqual(rows['missing']['attempts'], [])
        self.assertEqual(data['calls'], {'pass': 1, 'retry': 2, 'fail': 3, 'timeout': 2, 'zero': 3})
        self.assertTrue(all(row['url'] == row['id'] for row in data['output'] if row['id'] != 'missing'))


if __name__ == '__main__':
    unittest.main()
