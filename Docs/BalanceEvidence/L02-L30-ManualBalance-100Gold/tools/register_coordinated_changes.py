"""Record the exact externally owned files agreed in user-authorized coordination."""
from formal_tools import *
import datetime,shutil,sys
tag=sys.argv[1]if len(sys.argv)>1 else 'initial'
snapshot=REPORT/'audit/coordinated-code-snapshot'/tag
snapshot.mkdir(parents=True,exist_ok=False)
owner='01a16345-4801-78a0-b9d0-17d610469c4d'
source=ROOT/'Docs/EnemyDirectionReview/AdvancedHen/implementation_fingerprint.json'
their=json.loads(source.read_text(encoding='utf-8-sig'))
baseline=json.loads((REPORT/'audit/protected-files-before.json').read_text(encoding='utf-8'))
records={}
paths=['Assets/Scripts/Enemy/BaseEnemy.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Editor/EnemyDirectionPrefabBuilder.cs']
if 'Assets/Scripts/Enemy/EnemyDirectionalProfile.cs'in their:paths.append('Assets/Scripts/Enemy/EnemyDirectionalProfile.cs')
for path in paths:
    current=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    assert current==their[path].lower(),path
    records[path]=dict(originalBaselineSha256=baseline[path],frozenSha256=current,ownerThreadId=owner,scope='User-authorized AdvancedHen direction/flash/animation integration, explicitly coordinated and frozen before this batch')
    out=snapshot/path;out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,out)
record=dict(capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization='User explicitly authorized coordination with another task editing this project',ownerFingerprintSource=str(source.relative_to(ROOT)),ownerFingerprintSha256=hashlib.sha256(source.read_bytes()).hexdigest(),files=records)
current=REPORT/'audit/coordinated-external-changes.json'
if current.exists():
    previous=REPORT/f'audit/coordinated-external-changes-before-{tag}.json';assert not previous.exists();shutil.copy2(current,previous)
record['snapshot']=snapshot.relative_to(REPORT).as_posix()
current.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(source,snapshot/'owner-implementation-fingerprint.json')
print(len(paths),'agreed external code changes match their final frozen fingerprints; original baseline and previous registrations retained')
