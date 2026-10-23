"""Preserve six newly observed development layouts and complete wave records."""
from formal_tools import *
import subprocess,sys
selections=json.loads((REPORT/'audit/development-reference-selections.json').read_text(encoding='utf-8'))['levels']
for entry in selections:
 if entry['level']not in[9,10,19,24,25,27]:continue
 out=REPORT/f'L{entry["level"]:02}'/('首次成功-r4'if entry['level']==10 else'首次成功-r3')
 subprocess.run([sys.executable,'-X','utf8',str(REPORT/'tools/render_result_report.py'),str(REPORT/entry['source']),str(entry['sourceIndex']),str(out)],check=True,capture_output=True)
 subprocess.run([sys.executable,'-X','utf8',str(REPORT/'tools/render_development_stages.py'),str(REPORT/entry['source']),str(entry['sourceIndex']),str(out)],check=True,capture_output=True)
 print(entry['level'],'development report preserved')
