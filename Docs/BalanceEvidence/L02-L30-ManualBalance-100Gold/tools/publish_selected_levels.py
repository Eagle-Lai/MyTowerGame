"""Materialize the already selected complete proofs, one independent level at a time."""
from formal_tools import *
import subprocess, sys

selected=json.loads((REPORT/'audit/selected-final-proofs.json').read_text(encoding='utf-8'))
assert not selected['missingStrictTriples'] and {x['level']for x in selected['levels']}==set(range(2,31))
assert selected['runtimeContentHash']==runtime_hash()
for entry in sorted(selected['levels'],key=lambda x:x['level']):
    level=entry['level'];result=REPORT/entry['results'];notes=REPORT/f'L{level:02}/evidence/final-authored-notes.json'
    assert notes.is_file() and trial_inputs_match_current(result)
    completed=subprocess.run([sys.executable,'-X','utf8',str(REPORT/'tools/finalize_level.py'),
                              str(result),str(level),str(notes)],cwd=ROOT,check=True)
print('All29 selected final reports and layouts materialized')
