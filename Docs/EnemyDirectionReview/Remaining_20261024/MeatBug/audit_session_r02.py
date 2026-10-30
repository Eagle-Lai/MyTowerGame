from pathlib import Path
import json,subprocess,hashlib
base=Path('Docs/EnemyDirectionReview/Remaining_20261024').resolve();root=base.parents[2];d=base/'MeatBug'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
session=json.loads((d/'session_baseline_20261025.json').read_text(encoding='utf-8'))
old=set(session['git_status'].splitlines());now=set(subprocess.check_output(['git','status','--short'],encoding='utf-8').splitlines());added=sorted(now-old);removed=sorted(old-now)
allowed=['Assets/Prefabs/Enemy/Enemy_MeatBug.prefab','Assets/_UIAssets/Monsters/Insects/MeatBug/Directions']
unexpected=[x for x in added+removed if not any(a in x for a in allowed)]
protected={p:sha(root/p)==h for p,h in session['fingerprints'].items() if p!='Assets/Prefabs/Enemy/Enemy_MeatBug.prefab'}
broad=json.loads((base/'scope_MeatBug_20261025_r02.json').read_text(encoding='utf-8'));semantic=broad['semantics']['MeatBug'];exceptions=semantic['unexpected'];assert len(exceptions)==1 and exceptions[0]['kind']==114
fid=str(exceptions[0]['original_component_changed'])
def block(text):
 rows=text.splitlines();start=next(i for i,s in enumerate(rows) if s=='--- !u!114 &'+fid);end=next((i for i in range(start+1,len(rows)) if rows[i].startswith('--- !u!')),len(rows));return rows[start:end]
before=block((d/'before/Assets/Prefabs/Enemy/Enemy_MeatBug.prefab').read_text(encoding='utf-8-sig'));after=block((root/'Assets/Prefabs/Enemy/Enemy_MeatBug.prefab').read_text(encoding='utf-8-sig'))
expected=[s.replace('HeadRenderer: {fileID: 0}','HeadRenderer: {fileID: 2356903578807407913}') for s in before];ix=expected.index('  HeadSprites:');expected=expected[:ix+1]+['  - {fileID: -5673618120071735642, guid: 4b6418e9d3cbe1741ae3072e3245e2b9, type: 3}']*3
receiver_match=expected==after
art=root/'Assets/_UIAssets/Monsters/Insects/MeatBug/Directions';sprites=json.loads((art/'MeatBug_Directions.sprites.json').read_text(encoding='utf-8'))['sprites']
report={'basis':'session_baseline_20261025.json plus exact receiver repair_02; historical batch audit retained as FAIL, not rewritten','git_status_added':added,'git_status_removed':removed,'unexpected_new_status':unexpected,'original_sources_and_guids_unchanged':protected,'standard_semantic_audit':semantic,'explicit_exception':{'id':fid,'exact_expected_receiver_change':receiver_match,'reason':'Bind existing original Body to preserve integrated face and avoid missing head exception; no visual curve or sprite changes'},'sprites':len(sprites),'pass':not unexpected and all(protected.values()) and receiver_match}
(d/'scope_session_r02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['git_status_added','git_status_removed','unexpected_new_status','original_sources_and_guids_unchanged','explicit_exception','sprites','pass']},ensure_ascii=False));assert report['pass']