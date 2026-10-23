"""Run manually ONLY after explicit Unity handoff. Applies one authorized prefab's input art,
or the shared code batch. It cannot rebuild prefabs, operate Unity or modify tables.
"""
from pathlib import Path
import argparse,json,hashlib,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--shared',action='store_true');parser.add_argument('--name');args=parser.parse_args()
if args.shared==bool(args.name):raise ValueError('Choose --shared or one --name')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
snapshot={s['path']:s for s in json.loads((HERE/'source_snapshot.json').read_text(encoding='utf-8'))}
jobs=[]
if args.shared:
    for relative in ['Assets/Scripts/Enemy/EnemyDirectionalProfile.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Editor/EnemyDirectionPrefabBuilder.cs','Assets/Editor/EnemyDirectionalRigBuilder.cs','Assets/Editor/EnemyDirectionBatchReview.cs']:
        source=HERE/'staged_code'/(Path(relative).name+'.txt');target=ROOT/relative
        current=sha(target);expected=snapshot.get(relative,{}).get('sha256')
        if current!=expected and current!=sha(source):raise ValueError('Production drift: merge before application: '+relative)
        jobs.append((source,target))
else:
    data=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))
    t=next((t for t in data['targets'] if t['name']==args.name),None)
    if t is None:raise ValueError('Character not in authorized next ten')
    for suffix in ['.png','.sprites.json','.layout.json']:
        source=HERE/args.name/'staged_art'/(args.name+'_Directions'+suffix)
        if not source.is_file():raise FileNotFoundError('Missing real art: '+str(source))
        jobs.append((source,ROOT/t['art_dir']/source.name))
    for relative,expected in t['files'].items():
        if relative==t['battle']:continue
        if sha(ROOT/relative)!=expected:raise ValueError('Original source/GUID drift: '+relative)
log=[]
for source,target in jobs:
    if not source.is_file():raise FileNotFoundError(source)
    if not target.resolve().is_relative_to(ROOT/'Assets'):raise ValueError('Destination outside permitted asset roots')
    log.append({'path':target.relative_to(ROOT).as_posix(),'before':sha(target),'staged':sha(source)})
# All preconditions pass before the first production mutation. Existing .meta files are untouched.
for (source,target),entry in zip(jobs,log):
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(source.read_bytes());entry['after']=sha(target)
output=HERE/'application_records';output.mkdir(exist_ok=True)
stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
(output/(stamp+('_shared' if args.shared else '_'+args.name)+'.json')).write_text(json.dumps(log,indent=2),encoding='utf-8')
print(json.dumps(log,indent=2))
