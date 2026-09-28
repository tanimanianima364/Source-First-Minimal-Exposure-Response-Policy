from pathlib import Path
import json,hashlib,subprocess
p=Path('eval-tasks/format-and-diversity-2026-09-28');d=json.loads((p/'plan.json').read_text());r=Path('eval-results/chatgpt-task-diversity-2026-09-28');rows=json.loads((r/'manifest.json').read_text())
for f,h in d['inputs_and_rubric'].items(): assert hashlib.sha256((p/f).read_bytes()).hexdigest()==h,f
for x in rows:
 t=x['case']+'-'+x['condition'];v=d['conditions'][x['condition']];canonical=subprocess.check_output(['git','show',v['commit']+':PROMPT.md'])
 assert (r/(t+'-saved.txt')).read_bytes()==canonical[:-1],t
 assert (r/(t+'-composer.txt')).read_text()==(p/(x['case']+'.txt')).read_text(),t
 assert hashlib.sha256((r/x['raw']).read_bytes()).hexdigest()==x['raw_sha256']
 for suffix in ['before','after','persisted']:
  flags=json.loads((r/(t+'-'+suffix+'-controls.json')).read_text())['Flags']; assert len(flags)==8 and all(v['State']=='Off' for v in flags),t
 opts=json.loads((r/(t+'-model-selection.json')).read_text())['Options'];assert [o['Name'] for o in opts if o['Selected']]==['GPT-5.6 Sol']
 assert (r/(t+'-model.png')).stat().st_size>0 and (r/(t+'-mode.png')).stat().st_size>0
print('Verified',len(rows),'collected replies; expected',d['planned_replies'])
assert len(rows)==d['planned_replies']==22
assert len({(x['case'],x['condition']) for x in rows})==22
deviations=json.loads((r/'order-deviations.json').read_text())['deviations']
for case,order in d['order'].items():
    actual=[x['condition'] for x in sorted([x for x in rows if x['case']==case],key=lambda x:x['submitted'])]
    if actual!=order:
        assert deviations[case]=={'planned':order,'actual':actual}
    for x in rows:
        if x['case']==case: assert x['planned_order_followed']==(actual==order)
g=json.loads((r/'grades.json').read_text());assert len(g)==22
assert all(x['content']==('fail' if x['case'] in ['csv','distributed'] or (x['case'],x['condition'])==('sql','PR5') else 'pass') for x in g)
original=json.loads((r/'original-controls.json').read_text());restored=json.loads((r/'restoration.json').read_text())
assert {x['Name']:x['State'] for x in original}=={x['Name']:x['State'] for x in restored['Flags']}
assert restored['InstructionsMatchBackup'] and restored['InstructionCharacters']==0
assert json.loads((r/'closed-windows.json').read_text())['Remaining']==0
print('Order deviations, recorded grades, restoration and closure verified')

# SQL is a post-response diagnostic, not a replacement for frozen test results.
for condition, code in [('PR5', 1), ('A-ja', 0)]:
    log=(r/('sql-'+condition+'-row-factory-diagnostic.log')).read_text()
    assert 'ISOLATED_RUN_EXIT='+str(code) in log
    assert 'returned: '+('Row' if condition=='PR5' else 'tuple') in log
assert '| sql |' not in (r/'README.md').read_text()

assert all(x['status']=='human confirmed; 2026-09-28' and x.get('human_confirmation') for x in g)
assert '| 未確認 |' not in (r/'HUMAN-REVIEW.md').read_text()
