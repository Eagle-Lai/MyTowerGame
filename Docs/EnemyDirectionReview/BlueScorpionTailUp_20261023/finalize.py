from pathlib import Path
import json,hashlib,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
a=json.loads((HERE/'scope_audit.json').read_text(encoding='utf-8'))
assert a['pass'] and len(a['changed_files'])==9
assert a['unchanged_other_battle_prefabs']==118
assert all(sha(ROOT/c['path'])==c['after_sha256'] for c in a['changed_files'])
assert all(sha(HERE.parent/p)==h for p,h in a['history_identity'].items())
sem=json.loads((HERE.parent/'Batch01_10/scope_tailup_r01.json').read_text(encoding='utf-8'))
assert all(v['pass'] for v in sem['prefab_semantics'].values())
artifacts=['baseline.json','source_snapshot.json','implementation_manifest.json','final_fingerprints.json','scope_audit.json','scope_audit_unclassified.json','editor_validation.json','focused_media_manifest.json','close_media_manifest.json','installed.txt','up_walk_close.gif','up_walk_close.png','tail_before_after.gif','up_attack_fixed.gif','up_death_fixed.gif','README.md']
report={'recorded_at':datetime.datetime.now().astimezone().isoformat(),'character':'BlueScorpion','scope':'Up tail curls toward screen top from posterior abdomen','status':'installed_waiting_for_user_art_review','task_changed_files':9,'unchanged_other_battle_prefabs':118,'runtime':a['runtime'],'passes':sum(r['pass'] for r in a['runtime']),'failures':sum(r['fail'] for r in a['runtime']),'actual_frames':sum(r['frames'] for r in a['runtime']),'history_identity_unchanged':a['history_identity'],'concurrent_external_changes':a['concurrent_external_changes'],'workspace_no_external_drift':False,'artifacts_sha256':{p:sha(HERE/p) for p in artifacts},'unity_released':True,'next_action':'Wait for user art review; do not begin additional enemies','unperformed':['APK/device','release bundle build/readback','long battle','balance regression']}
(HERE/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','passes','failures','actual_frames','task_changed_files']}))
