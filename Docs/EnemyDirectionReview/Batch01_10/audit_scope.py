"""Read-only production scope + per-component prefab audit against this batch's LOCAL baseline."""
from pathlib import Path
import re,json,hashlib,argparse,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--installed',nargs='*',default=[]);parser.add_argument('--out',default='scope_preinstall.json');args=parser.parse_args()
baseline=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))
targets={t['name']:t for t in baseline['targets']}
if not set(args.installed)<=set(targets):raise ValueError('Only authorized names are supported')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None
def blocks(text):return {int(m[2]):{'kind':int(m[1]),'text':m[3]} for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S)}
def fid(text,key):
    m=re.search(re.escape(key)+r': \{fileID: (-?\d+)',text);return int(m[1]) if m else 0
def node_name(text):
    m=re.search(r'^  m_Name: (.*)$',text,re.M);return m[1] if m else ''
def canonical(body):
    body=re.sub(r'^  m_RootOrder: .*\n','',body,flags=re.M)
    return body.strip()
def semantic(name):
    original=HERE/name/'reference'/('Enemy_'+name+'.prefab');current=ROOT/targets[name]['battle']
    a=blocks(original.read_text(encoding='utf-8-sig'));b=blocks(current.read_text(encoding='utf-8-sig'))
    shadow_go={i for i,v in a.items() if v['kind']==1 and node_name(v['text'])=='Shadow'}
    shadow_ids=shadow_go|{i for i,v in a.items() if fid(v['text'],'m_GameObject') in shadow_go}
    new_ids=set(b)-set(a);removed=set(a)-set(b)
    changes=[];fail=[]
    if removed!=shadow_ids:fail.append({'unexpected_removed_ids':sorted(removed-shadow_ids),'shadow_ids_remaining':sorted(shadow_ids-removed)})
    root_go=next(i for i,v in a.items() if v['kind']==1 and node_name(v['text'])=='Enemy_'+name)
    root_tr=next(i for i,v in a.items() if v['kind']==4 and fid(v['text'],'m_GameObject')==root_go)
    hp_go={i for i,v in a.items() if v['kind']==1 and node_name(v['text'])=='HpBar'}
    hp_tr={i for i,v in a.items() if v['kind']==4 and fid(v['text'],'m_GameObject') in hp_go}
    while True:
        more={i for i,v in a.items() if v['kind']==4 and fid(v['text'],'m_Father') in hp_tr}-hp_tr
        if not more:break
        hp_tr|=more
    hp_go|={fid(a[i]['text'],'m_GameObject') for i in hp_tr}
    new_go={i for i in new_ids if b[i]['kind']==1}
    groups={i for i in new_go if node_name(b[i]['text'])=='DirectionVisual'}
    group_tr={i for i in new_ids if b[i]['kind']==4 and fid(b[i]['text'],'m_GameObject') in groups}
    if len(groups)!=1:fail.append({'direction_group_count':len(groups)})
    while True:
        more={i for i in new_ids if b[i]['kind']==4 and fid(b[i]['text'],'m_Father') in group_tr}-group_tr
        if not more:break
        group_tr|=more
    group_go={fid(b[i]['text'],'m_GameObject') for i in group_tr}
    if new_go-group_go:fail.append({'new_nodes_outside_direction_group':sorted(new_go-group_go)})
    for i in new_ids:
        v=b[i];owner=fid(v['text'],'m_GameObject')
        if v['kind']==114 and owner==root_go:
            visual_meta=(ROOT/'Assets/Scripts/Enemy/EnemyDirectionalVisual.cs.meta').read_text(encoding='utf-8')
            visual_guid=re.search(r'^guid: (\w+)',visual_meta,re.M)[1]
            if ('guid: '+visual_guid) not in v['text']:fail.append({'unexpected_root_script':i})
            continue
        if v['kind']==1 or owner in new_go:continue
        fail.append({'unexpected_new_component':i,'kind':v['kind']})
    for i,v in a.items():
        if i in shadow_ids or i not in b:continue
        before=v['text'];after=b[i]['text'];kind=v['kind'];permitted=[]
        if i==root_go:
            for new in new_ids:after=re.sub(r'^  - component: \{fileID: '+str(new)+r'\}\n','',after,flags=re.M)
            permitted.append('new opt-in direction component')
        if i==root_tr:
            for missing in shadow_ids:before=re.sub(r'^  - \{fileID: '+str(missing)+r'\}\n','',before,flags=re.M)
            for new in new_ids:after=re.sub(r'^  - \{fileID: '+str(new)+r'\}\n','',after,flags=re.M)
            permitted.append('Shadow child removed; DirectionVisual child added')
        if kind==95:
            before=re.sub(r'^  m_Controller: .*$', '  m_Controller: DIRECTION_CONTROLLER',before,flags=re.M)
            after=re.sub(r'^  m_Controller: .*$', '  m_Controller: DIRECTION_CONTROLLER',after,flags=re.M)
            permitted.append('dedicated controller')
        if kind==212 and fid(v['text'],'m_GameObject') not in hp_go:
            before=re.sub(r'(  m_Materials:\n)(?:  - .*\n)+',r'\1  - FLASH_MATERIAL\n',before)
            after=re.sub(r'(  m_Materials:\n)(?:  - .*\n)+',r'\1  - FLASH_MATERIAL\n',after)
            permitted.append('shared flash shader material reference')
        if canonical(before)!=canonical(after):fail.append({'original_component_changed':i,'kind':kind,'owner':fid(v['text'],'m_GameObject')})
        elif v['text']!=b[i]['text']:changes.append({'id':i,'allowed':permitted,'rootOrder_normalized':True})
    return {'baseline_sha256':sha(original),'current_sha256':sha(current),'removed_shadow_ids':sorted(shadow_ids),'added_components':len(new_ids),'allowed_original_component_changes':changes,'unexpected':fail,'pass':not fail}

changed=[];unexpected=[]
allowed_paths={targets[n]['battle'] for n in args.installed}
for item in baseline['prefabs']:
    current=sha(ROOT/item['path'])
    if current!=item['sha256']:
        changed.append({'path':item['path'],'before':item['sha256'],'after':current})
        if item['path'] not in allowed_paths:unexpected.append(item['path'])
protected=[]
for target in targets.values():
    for path,expected in target['files'].items():
        if path.endswith('.prefab') and path==target['battle']:continue
        current=sha(ROOT/path)
        if current!=expected:protected.append({'path':path,'before':expected,'after':current})
animation_path=HERE/'shared_animation_baseline.json'
if not animation_path.exists():
    paths=sorted({p for t in targets.values() for p in (ROOT/t['controller']).parent.rglob('*') if p.is_file()})
    animation_path.write_text(json.dumps({'observed_at':datetime.datetime.now().isoformat(),'note':'Captured during Docs-only freeze, before any batch application; later than initial source baseline.','files':{p.relative_to(ROOT).as_posix():sha(p) for p in paths}},indent=2),encoding='utf-8')
animation=json.loads(animation_path.read_text(encoding='utf-8'))
animation_drift=[p for p,expected in animation['files'].items() if sha(ROOT/p)!=expected]
source_snapshot=json.loads((HERE/'source_snapshot.json').read_text(encoding='utf-8'))
source_drift=[s['path'] for s in source_snapshot if sha(ROOT/s['path'])!=s['sha256']]
report={'observed_at':datetime.datetime.now().isoformat(),'baseline':'local_baseline.json; no Git reset/pull','installed_declared':args.installed,'prefab_count':len(baseline['prefabs']),'changed_prefabs':changed,'untouched_prefabs':119-len(changed),'unexpected_prefab_changes':unexpected,'original_sources_or_GUID_drift':protected,'shared_animation_drift':animation_drift,'production_source_drift_since_local_baseline':source_drift,'prefab_semantics':{n:semantic(n) for n in args.installed},'note':'Read-only scope audit; no runtime/compilation/art-approval claim.'}
output=(HERE/args.out).resolve()
if not output.is_relative_to(HERE):raise ValueError('Output must stay under this Docs batch')
output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['installed_declared','prefab_count','untouched_prefabs','unexpected_prefab_changes','original_sources_or_GUID_drift','shared_animation_drift','production_source_drift_since_local_baseline']},ensure_ascii=False))
