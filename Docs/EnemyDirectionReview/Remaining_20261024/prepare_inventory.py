"""Read current local files; snapshot all code and production identities. Write Docs only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, re, shutil, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APPROVED = {'AdvancedHen','Bat','BattlePanther','Bear','BearMounted','BlackBear','BlackBoar','BlackWolf','BlueScorpion','Boar','BoarMounted'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def save(p, value): p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if (HERE/'local_baseline.json').exists(): raise SystemExit('Baseline already exists; refusing to overwrite.')
files = sorted(p for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file())
codes = [p for p in files if p.suffix in ['.cs','.asmdef','.asmref'] or p.name in ['manifest.json','packages-lock.json']]
save(HERE/'source_snapshot.json',[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'content':p.read_text(encoding='utf-8-sig')} for p in codes])
save(HERE/'production_fingerprints_before.json',{p.relative_to(ROOT).as_posix():sha(p) for p in files})
meta = {}
for p in (ROOT/'Assets/_UIAssets/Monsters').rglob('*.meta'):
    m = re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig'),re.M)
    if m: meta[m.group(1)] = p.with_suffix('')
prefabs = sorted((ROOT/'Assets/Prefabs/Enemy').glob('*.prefab'),key=lambda p:p.name)
targets = []
for index,battle in enumerate(prefabs):
    name = battle.stem.removeprefix('Enemy_')
    if name in APPROVED: continue
    text = battle.read_text(encoding='utf-8-sig')
    original = list((ROOT/'Assets/_UIAssets/Monsters').rglob(name+'.prefab'))
    if len(original) != 1: raise ValueError('Source prefab must be unique: '+name+str(original))
    source = original[0]
    source_text = source.read_text(encoding='utf-8-sig')
    atlas = source.with_suffix('.png')
    if not atlas.is_file():
        atlases = {meta[g] for g in re.findall(r'm_Sprite: \{fileID: -?\d+, guid: (\w+)',source_text) if g in meta and meta[g].suffix=='.png' and meta[g].parent==source.parent}
        if len(atlases)!=1: raise ValueError('Ambiguous referenced authoritative atlas: '+name+str(atlases))
        atlas = next(iter(atlases))
    ctrl = meta[re.search(r'm_Controller: \{fileID: \d+, guid: (\w+)',source_text).group(1)]
    ref = HERE/name/'reference'; ref.mkdir(parents=True,exist_ok=True)
    for p in [source,source.with_suffix('.prefab.meta'),atlas,atlas.with_suffix('.png.meta'),battle,battle.with_suffix('.prefab.meta')]: shutil.copy2(p,ref/p.name)
    targets.append({'index':index,'name':name,'source':source.relative_to(ROOT).as_posix(),'battle':battle.relative_to(ROOT).as_posix(),
        'art_dir':source.parent.relative_to(ROOT).as_posix()+'/Directions','controller':ctrl.relative_to(ROOT).as_posix(),'atlas':atlas.relative_to(ROOT).as_posix(),
        'family':source.parent.parent.name,'nodes':re.findall(r'^  m_Name: (.+)$',source.read_text(encoding='utf-8-sig'),re.M)})
save(HERE/'local_baseline.json',{'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'authorization':'用户要求继续处理剩余所有预制体，并集中所有GIF','approved':sorted(APPROVED),'targets':targets,'code_files':len(codes),'production_files':len(files)})
save(HERE/'progress.json',{'status':'in_progress','authorized_count':len(targets),'current':'BugQueen','items':[dict(index=t['index'],name=t['name'],status='not_started') for t in targets]})
(HERE/'git_status_before.txt').write_text(subprocess.run(['git','status','--short'],cwd=ROOT,capture_output=True,text=True,check=True).stdout,encoding='utf-8')
renderer=(HERE.parent/'Batch01_10/render_source_reference.py').read_text(encoding='utf-8')
renderer=renderer.replace("contact=Image.new('RGB',(1600,1100)","contact=Image.new('RGB',(1600,math.ceil(len(targets)/5)*550)")
renderer=renderer.replace("source.with_suffix('.png')","ROOT/t['atlas']").replace("source.with_suffix('.png.meta')","ROOT/(t['atlas']+'.meta')")
(HERE/'render_source_reference.py').write_text(renderer,encoding='utf-8')
print(json.dumps({'remaining':len(targets),'production_files':len(files),'code_files':len(codes),'families':sorted(set(t['family'] for t in targets))}))
