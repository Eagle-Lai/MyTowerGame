"""Preserve actual official exporter success entries; never run or replace an export."""
from formal_tools import *
import datetime

source = pathlib.Path('C:/Users/Administrator/AppData/Local/Unity/Editor/Editor.log')
lines = source.read_text(encoding='utf-8', errors='replace').split('\n')
indices = [i for i, s in enumerate(lines) if s.startswith('[Luban] 导出成功：')]
entries = []
for i in indices[-2:]:
    excerpt = []
    for line in lines[i:i+40]:
        excerpt.append(line)
        if line.startswith('(Filename: Assets/Editor/LubanExporter.cs'): break
    assert any('FTProject.EditorTools.LubanExporter:ExportFromMenu' in line for line in excerpt)
    assert any('Assets/Gen' in line and 'Assets/ConfigJson' in line for line in excerpt)
    entries.append(dict(sourceLine=i+1, rawLog=excerpt))
assert len(entries) == 2
audit = json.loads((REPORT/'audit/formal-integrity-final.json').read_text(encoding='utf-8'))
assert audit['runtimeHash'] == runtime_hash() and audit['sourceExportMatch'] and audit['sealMatch']
out = REPORT/'audit/final-formal-export-log.json'
assert not out.exists()
record = dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              source=str(source), officialEntry='FTProject.EditorTools.LubanExporter.ExportFromMenu',
              runtimeContentHash=runtime_hash(), entries=entries,
              currentOutputSha256={k:hashlib.sha256((ROOT/f'Assets/ConfigJson/{k}.json').read_bytes()).hexdigest()
                                   for k in KEYS+['tblevelrating']},
              correspondence='The last two real exporter success entries are preserved. Current output bytes and source/export agreement are recorded separately; log capture does not run a new export.',
              sourceExportAudit='formal-integrity-final.json')
out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
print('Official exporter success entries preserved at Editor.log lines', [e['sourceLine'] for e in entries])
