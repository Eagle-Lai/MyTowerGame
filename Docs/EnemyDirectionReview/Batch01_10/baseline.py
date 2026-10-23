"""Snapshot local sources and target references. Writes Docs only, never project assets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, re, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAMES = ['Bat','BattlePanther','Bear','BearMounted','BlackBear','BlackBoar','BlackWolf','BlueScorpion','Boar','BoarMounted']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def save(name, data):
    (HERE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if (HERE/'local_baseline.json').exists():
    raise SystemExit('Baseline exists; refusing to overwrite the local starting point.')
codes = sorted(p for folder in ['Assets','Packages'] for p in (ROOT/folder).rglob('*') if p.is_file() and
               (p.suffix in ['.cs','.asmdef','.asmref'] or p.name in ['manifest.json','packages-lock.json']))
sources = [{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'content':p.read_text(encoding='utf-8-sig')} for p in codes]
prefabs = sorted((ROOT/'Assets/Prefabs/Enemy').glob('*.prefab'),key=lambda p:p.name)
assert [p.stem.removeprefix('Enemy_') for p in prefabs[1:11]] == NAMES
all_meta = {}
for p in (ROOT/'Assets/_UIAssets/Monsters/_Common/Animations').rglob('*.meta'):
    m=re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig'),re.M)
    if m: all_meta[m.group(1)] = p.with_suffix('').relative_to(ROOT).as_posix()
targets=[]
for i,name in enumerate(NAMES,1):
    source=next((ROOT/'Assets/_UIAssets/Monsters').rglob(name+'.prefab'))
    battle=ROOT/f'Assets/Prefabs/Enemy/Enemy_{name}.prefab'
    text=battle.read_text(encoding='utf-8-sig')
    ctrl=re.search(r'm_Controller: \{fileID: \d+, guid: (\w+)',text).group(1)
    refs=[source,source.with_suffix('.prefab.meta'),source.with_suffix('.png'),source.with_suffix('.png.meta'),battle,battle.with_suffix('.prefab.meta')]
    directory=HERE/name/'reference';directory.mkdir(parents=True,exist_ok=True)
    for p in refs: (directory/p.name).write_bytes(p.read_bytes())
    entry={'index':i,'name':name,'source':source.relative_to(ROOT).as_posix(),'art_dir':source.parent.relative_to(ROOT).as_posix()+'/Directions',
           'battle':battle.relative_to(ROOT).as_posix(),'controller':all_meta[ctrl],
           'nodes':re.findall(r'^  m_Name: (.+)$',text,re.M),'files':{p.relative_to(ROOT).as_posix():sha(p) for p in refs}}
    targets.append(entry)
save('source_snapshot.json',sources)
save('local_baseline.json',{'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
     'sources':len(sources),'prefabs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in prefabs],
     'targets':targets,'approved_example':'AdvancedHen R3','authorized_next_count':10})
save('progress.json',{'status':'preparing_docs_waiting_for_safe_handoff','approved_example':True,'authorized_next_count':10,
     'current_index':1,'next_after_batch':'Enemy_BugQueen.prefab','items':[{'index':t['index'],'name':t['name'],'status':'not_started'} for t in targets]})
(HERE/'git_status_before.txt').write_text(subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True,check=True).stdout,encoding='utf-8')
print(json.dumps({'sources':len(sources),'prefabs':len(prefabs),'targets':[{k:v for k,v in t.items() if k in ['index','name','source','controller']} for t in targets]},ensure_ascii=False,indent=2))
