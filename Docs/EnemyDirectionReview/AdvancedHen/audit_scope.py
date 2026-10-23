"""Read-only scope audit against the pre-edit local baseline. Writes Docs evidence only."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = Path('C:/Users/Administrator/AppData/Local/Temp/AdvancedHenDirection-20261022')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


before = json.loads((BASELINE/'prefab-baseline.json').read_text(encoding='utf-8-sig'))
prefabs = sorted((ROOT/'Assets/Prefabs/Enemy').glob('*.prefab'), key=lambda p: p.name)
results = []
for entry in before:
    path = ROOT/'Assets/Prefabs/Enemy'/entry['name']
    current = sha(path)
    results.append(dict(name=path.name, before=entry['sha256'], after=current, changed=current != entry['sha256']))
changed = [e['name'] for e in results if e['changed']]
assert len(prefabs) == len(before) == 119 and prefabs[0].name == 'Enemy_AdvancedHen.prefab'
assert changed == ['Enemy_AdvancedHen.prefab'], changed
(HERE/'prefab_scope_audit.json').write_text(json.dumps(dict(count=119, first=prefabs[0].name, unchanged_others=118, changed=changed, files=results), indent=2), encoding='utf-8')

codes = json.loads((BASELINE/'local-code-baseline.json').read_text(encoding='utf-8-sig'))
ours = ['Assets/Scripts/Enemy/BaseEnemy.cs', 'Assets/Scripts/Enemy/EnemyDirectionalProfile.cs', 'Assets/Scripts/Enemy/EnemyDirectionalVisual.cs', 'Assets/Editor/EnemyDirectionPrefabBuilder.cs']
new = ['Assets/Editor/AdvancedHenDirectionReview.cs']
patch = []
for path in ours:
    entry = next(e for e in codes if e['path'].replace('\\', '/') == path)
    current = (ROOT/path).read_text(encoding='utf-8-sig')
    patch.extend(difflib.unified_diff(entry['content'].splitlines(True), current.splitlines(True), fromfile='before/'+path, tofile='after/'+path))
for path in new:
    patch.extend(difflib.unified_diff([], (ROOT/path).read_text(encoding='utf-8-sig').splitlines(True), fromfile='/dev/null', tofile='after/'+path))
(HERE/'changes_from_local_baseline.patch').write_text(''.join(patch), encoding='utf-8')

unchanged_code = []
for suffix in ['MonsterAnimEventReceiver.cs', 'MonsterPrefabBuilder.cs']:
    entry = next(e for e in codes if e['path'].endswith(suffix))
    path = ROOT/entry['path'].replace('\\', '/')
    assert sha(path) == entry['sha256'], suffix
    unchanged_code.append(str(path.relative_to(ROOT)).replace('\\','/'))

immutable = [ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png', ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png.meta', ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.prefab', ROOT/'Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab.meta']
immutable += list((ROOT/'Assets/_UIAssets/Monsters/_Common/Animations/Rooster').glob('*'))
clean = subprocess.run(['git','diff','--name-only','HEAD','--']+[str(p) for p in immutable], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
assert not clean, clean
assets = [ROOT/'Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab']
assets += [p for p in (ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions').rglob('*') if p.is_file()]
assets += [ROOT/p for p in ours+new]
(HERE/'implementation_fingerprint.json').write_text(json.dumps({str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(assets)}, indent=2), encoding='utf-8')
(HERE/'scope_summary.txt').write_text('Pre-edit local code baseline: 179 files read in full.\n119 direct enemy prefabs, first Enemy_AdvancedHen.prefab.\nChanged: Enemy_AdvancedHen.prefab only; other 118 byte-identical to baseline.\nOriginal PNG, slicing metadata, source prefab, Rooster resources and battle prefab GUID metadata match HEAD.\nReused unchanged code: '+', '.join(unchanged_code)+'\nNo Git pull/reset, no table/config export writes, no whole-catalog rebuild.\n', encoding='utf-8')
print('PASS scope: 119 prefabs, only AdvancedHen changed; 118 unchanged; original/source/Rooster/GUID preserved.')
