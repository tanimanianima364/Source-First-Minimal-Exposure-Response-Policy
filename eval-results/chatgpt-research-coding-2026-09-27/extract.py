from pathlib import Path
import re,sys,hashlib,json
raw=Path(sys.argv[1]).read_bytes()
blocks=re.findall(rb'^```(?:python|py)[ \t]*\r?\n(.*?)^```[ \t]*(?:\r?\n|$)',raw,re.M|re.S)
assert len(blocks)==2, f'Expected exactly2 Python blocks; got {len(blocks)}; manual boundary audit required'
assert b'def init_db(' in blocks[0] and b'def apply_batch(' in blocks[0]
assert b'import inventory' in blocks[1] or b'from inventory import' in blocks[1]
out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
record=[]
for name,b in zip(['inventory.py','test_inventory.py'],blocks):
 (out/name).write_bytes(b);record.append({'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'raw_start':raw.index(b)})
(out/'extraction.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
