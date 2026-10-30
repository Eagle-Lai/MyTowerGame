"""Finalize ONE already visually reviewed character, with additive scope evidence."""
from pathlib import Path
from datetime import datetime
import hashlib, json, re, subprocess, sys
from mcp_call import Client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
name, manifest_path, visual_folder = sys.argv[1:4]
d = HERE / name
note = (d/'record_note_utf8.txt').read_text(encoding='utf-8-sig').strip()
if not note: raise ValueError('Actual visual observations required')
output = d/'final_validation_20261026.json'
if output.exists(): raise ValueError('Final evidence exists; inspect before retrying')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
base = json.loads((d/'incremental_before_20261026.json').read_text(encoding='utf-8'))['files']
changes = [{'path':p,'before':s,'after':sha(ROOT/p)} for p,s in base.items() if sha(ROOT/p)!=s]
reporter_side_effects=[]
unexpected=[]
for change in changes:
    if change['path']=='Assets/Prefabs/Enemy/Enemy_'+name+'.prefab': continue
    if (change['path']=='Assets/StreamingAssets/build_info'
        and sha(ROOT/'Assets/Reporter/Editor/ReporterEditor.cs')==base.get('Assets/Reporter/Editor/ReporterEditor.cs')
        and re.fullmatch(r'Build from .+ at .+', (ROOT/change['path']).read_text(encoding='utf-8'))):
        reporter_side_effects.append(dict(change,origin='Unmodified ReporterEditor writes build timestamp on entering Play'))
    else:
        unexpected.append(change)
if unexpected: raise ValueError('Unexpected incremental changes: '+str(unexpected))
targets = {t['name']:t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets']}
original = (HERE.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
exec(original[original.index('def sha('):original.index('changed=[];unexpected=[]')])
sem = semantic(name)
if not sem['pass']: raise ValueError('Prefab semantics failed: '+str(sem))
manifest = json.loads((d/manifest_path).read_text(encoding='utf-8'))
drift = [x['path'] for x in manifest['changes'] if sha(ROOT/x['path']) != x['after']]
if drift: raise ValueError('Final installed assets changed: '+str(drift))
legacy = max(HERE.glob('scope_'+name+'_*.json'),key=lambda p:p.stat().st_mtime)
lr = json.loads(legacy.read_text(encoding='utf-8'))
prior = json.loads((HERE/'PirateBoar/scope_incremental_20261026.json').read_text(encoding='utf-8'))
known = {x['path']:x.get('after') for x in prior['legacy_classification']}
new_legacy = [x for x in lr['unexpected'] if known.get(x['path']) != x.get('after')]
if new_legacy: raise ValueError('New unexpected full-scope changes: '+str(new_legacy))
scope = {'baseline':'incremental_before_20261026.json','incremental_changes':changes,
         'unexpected_incremental':unexpected,'allowed_incremental_side_effects':reporter_side_effects,
         'prefab_semantics':sem,'legacy_audit':legacy.name,
         'legacy_pass':lr['pass'],'legacy_unexpected_count':len(lr['unexpected']),
         'new_unexpected_vs_preexisting_legacy':new_legacy,'installed_asset_drift':drift,
         'note':'One character at a time. Historical full-scope failures preserved; no baseline reset.'}
(d/'scope_incremental_20261026.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
c=Client();project=c.identity();state=c.resource('mcpforunity://editor/state')
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
compiler=c.tool('execute_code',{'action':'execute','code':'return UnityEditor.EditorUtility.scriptCompilationFailed;'})
v=compiler.get('structuredContent') or json.loads(compiler['content'][0]['text'])
if v['data']['result'] is not False: raise ValueError('Compilation failed')
data=state['data']
if data['editor']['play_mode']['is_playing'] or not data['advice']['ready_for_tools']: raise ValueError('Editor has not returned ready')
runtime=json.loads((d/'runtime_summary.json').read_text(encoding='utf-8'))
if runtime['passes']!=168 or runtime['failures']!=0: raise ValueError('Expected final two successful rounds')
report={'observed_at':datetime.now().isoformat(),'project':project,'final_install_manifest':manifest_path,
        'state':state,'errors':errors,'script_compilation_failed':compiler,'installed_asset_drift':drift,
        'runtime_summary_sha256':sha(d/'runtime_summary.json'),'protocol_history':c.history}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
visual={'status':'completed_pending_user_art_review','note':note,
        'viewed_sheets':[p.name for p in (d/visual_folder).glob('*.png')],
        'review_method':'Chronological actual PNG samples, cycle and angry details; no live GIF playback',
        'source_manifest':'sources.json','final_install_manifest':manifest_path}
(d/visual_folder/'review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
subprocess.run([sys.executable,str(HERE/'record_review.py'),name,note],check=True)
print(json.dumps({'name':name,'prefab_semantics':sem['pass'],'incremental_prefabs':[x['path'] for x in changes],
                  'allowed_editor_side_effects':reporter_side_effects,
                  'compiler_failed':v['data']['result'],'errors':errors.get('structuredContent'),
                  'runtime':runtime['runtime'],'frames':runtime['actual_frames']},ensure_ascii=False))
