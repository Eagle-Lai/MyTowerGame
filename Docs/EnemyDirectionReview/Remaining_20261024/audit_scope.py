"""Read-only full-production and original-component audit against this run's local baseline."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
baseline=json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
targets={t['name']:t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets']}
installed=[name for name in targets if (HERE/name/'installed_manifest.json').exists()]
# Reuse the already established per-component YAML comparison, not a second looser implementation.
original=(HERE.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
definitions=original[original.index('def sha('):original.index('changed=[];unexpected=[]')]
import re
exec(definitions)
editor_manifest=json.loads((HERE/'editor_extension_manifest.json').read_text(encoding='utf-8'))
allowed={x['path'] for x in editor_manifest}|{x['path']+'.meta' for x in editor_manifest}
for name in installed:
    allowed.add(targets[name]['battle'])
current_files={p.relative_to(ROOT).as_posix():p for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changed=[];unexpected=[];editor_side_effects=[]
for path in sorted(set(baseline)|set(current_files)):
    before=baseline.get(path);after=sha(ROOT/path)
    if before==after:continue
    art_change=any(path.startswith(targets[n]['art_dir']+'/') or path==targets[n]['art_dir']+'.meta' for n in installed)
    reporter_side_effect=path=='Assets/StreamingAssets/build_info' and sha(ROOT/'Assets/Reporter/Editor/ReporterEditor.cs')==baseline['Assets/Reporter/Editor/ReporterEditor.cs'] and re.fullmatch(r'Build from .+ at .+', (ROOT/path).read_text(encoding='utf-8')) is not None
    allowed_change=path in allowed or art_change or reporter_side_effect
    entry={'path':path,'before':before,'after':after,'allowed':allowed_change}
    changed.append(entry)
    if reporter_side_effect:editor_side_effects.append(dict(entry,origin='Unmodified ReporterEditor writes build timestamp on entering Play; not an artwork edit'))
    if not allowed_change:unexpected.append(entry)
semantics={name:semantic(name) for name in installed}
report={'installed':installed,'changes':changed,'unexpected':unexpected,'automatic_editor_side_effects':editor_side_effects,'semantics':semantics,'pass':not unexpected and all(x['pass'] for x in semantics.values()),'basis':'local baseline; no remote pull/reset; no runtime validation claimed'}
output=HERE/(sys.argv[1] if len(sys.argv)>1 else 'scope_current.json')
if output.parent!=HERE:raise ValueError('Output outside this Docs run')
if output.exists():raise ValueError('Audit record exists; use a new name')
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pass':report['pass'],'installed':installed,'changes':len(changed),'unexpected':unexpected,'semantic_failures':{n:s['unexpected'] for n,s in semantics.items() if not s['pass']}},ensure_ascii=False))
