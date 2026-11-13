"""Read-only source/export baseline for this authorized L02 W5-W25 edit."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/(sys.argv[1] if len(sys.argv)>1 else 'Library/BalanceStage/trusted-terminal-design-20261109')
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/'scope-before.json'
if target.exists():
    raise SystemExit('Baseline already exists; preserve it')
sources={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in (ROOT/'Luban/Config/Datas').rglob('*.xlsx')}
exports={p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'mtimeNs':p.stat().st_mtime_ns,
                  'rows':json.loads(p.read_text(encoding='utf-8-sig'))}
         for p in (ROOT/'Assets/ConfigJson').glob('*.json')}
target.write_text(json.dumps({'sources':sources,'exports':exports},ensure_ascii=False),encoding='utf-8')
print(json.dumps({'sourceWorkbooks':len(sources),'exportFiles':len(exports),'baseline':str(target)}))
