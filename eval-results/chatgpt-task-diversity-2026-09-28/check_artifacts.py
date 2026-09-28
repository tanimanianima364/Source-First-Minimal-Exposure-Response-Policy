"""Extract verbatim Python blocks and reuse the existing isolated execution runner."""
import json,re,shutil,subprocess,sys
from pathlib import Path
case,condition=sys.argv[1:];tag=case+'-'+condition
root=Path('eval-results/chatgpt-task-diversity-2026-09-28');out=root/tag;out.mkdir(exist_ok=True)
raw=(root/(tag+'.md')).read_text(); blocks=re.findall(r'^```(?:python|py)[^\n]*\n(.*?)^```',raw,re.S|re.M)
assert blocks,'no Python fences'
(out/'inventory.py').write_text('\n\n'.join(blocks))
(out/'test_inventory.py').write_text('import inventory\n')
(out/'extraction.json').write_text(json.dumps({'source':tag+'.md','method':'Top-level Python fenced blocks concatenated verbatim; indented explanatory fragments excluded; no repairs','blocks':len(blocks)},indent=2)+'\n')
stage=Path('/tmp/source-first-format-pr5/sandbox');stage.mkdir(parents=True,exist_ok=True)
runner=Path('eval-results/chatgpt-research-coding-2026-09-27/checks/run.py').read_text()
if 'import pytest' in raw:
 runner=runner.replace("'PYTHONPATH', '/candidate',", "'PYTHONPATH', '/candidate:/deps', '--setenv', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1', '--ro-bind', '/home/tanima/.local/lib/python3.11/site-packages', '/deps',")
if 'from amounts import' in raw:
 (out/'inventory.py').write_text(blocks[0])
 (out/'amounts.py').write_text(blocks[0])
 (out/'test_inventory.py').write_text(blocks[-1])
 (out/'example.py').write_text(blocks[1])
 (out/'extraction.json').write_text(json.dumps({'source':tag+'.md','method':'Verbatim blocks; first block as amounts.py (and inventory.py for independent checker), last block as test_inventory.py; middle example separately preserved','blocks':len(blocks)},indent=2)+'\n')
 runner=runner.replace("('inventory.py', 'test_inventory.py')", "('inventory.py', 'test_inventory.py', 'amounts.py')")
(stage/'run.py').write_text(runner)
check=Path('eval-tasks/format-and-diversity-2026-09-28/checks.py').read_text().replace("CASE = 'duration'",'CASE = '+repr(case))
(stage/'test_contract.py').write_text(check)
runs=[('independent',[]),('examples',[])] if case in ['csv','duration','sql','rootcause'] else [('examples',[])]
exit_code=0
for label,args in runs:
 if label=='examples':
  example="import runpy\nrunpy.run_path('/candidate/inventory.py', run_name='__main__')\n"
  if 'import pytest' in raw: example="import pytest\nraise SystemExit(pytest.main(['/candidate/inventory.py', '-q', '-p', 'no:cacheprovider']))\n"
  if 'from amounts import' in raw: example=example.replace('/candidate/inventory.py','/candidate/test_inventory.py')
  (stage/'test_contract.py').write_text(example)
 proc=subprocess.run([sys.executable,str(stage/'run.py'),str(out),*args],capture_output=True,text=True)
 (root/(tag+'-'+label+'.log')).write_text(proc.stdout+proc.stderr)
 print(tag,label,proc.returncode)
 exit_code=exit_code or proc.returncode

raise SystemExit(exit_code)
