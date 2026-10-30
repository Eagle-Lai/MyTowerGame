from session_winterwarg import *
from audit_current import audit
import shutil
owner();assert (D/'installed_manifest.json').exists() and not (D/'installed_repair_art_r02_20261029.json').exists()
t=read(D/'incremental_before_20261029.json')['target'];p0=read(D/'preplay_version_binding_art_r01_20261029.json')
assert all(sha(ROOT/p)==s for p,s in p0['production_fingerprints'].items())
c=Client();project=c.identity();idle(probe(c));assert audit()['pass']
backup=D/'production_before_art_r02';assert not backup.exists();backup.mkdir()
shutil.copytree(ROOT/t['art_dir'],backup/'Directions');shutil.copy2(ROOT/t['battle'],backup/Path(t['battle']).name)
before={p:s for p,s in snapshot().items() if p in p0['production_fingerprints']}
for suffix in ['.png','.sprites.json','.layout.json']:
    p=D/'staged_art'/(NAME+'_Directions'+suffix);shutil.copy2(p,ROOT/t['art_dir']/p.name)
r=c.tool('refresh_unity',{'mode':'force','scope':'assets','compile':'none','wait_for_ready':True});c.identity()
code='FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("WinterWarg"); FTProject.EditorTools.EnemyDirectionSpec spec; FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("WinterWarg",out spec); string report; bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report); System.IO.File.WriteAllText("'+(D/'installed_verify_art_r02.txt').relative_to(ROOT).as_posix()+'",report);return Newtonsoft.Json.JsonConvert.SerializeObject(new {pass=pass,report=report});'
verification=result(c.tool('execute_code',{'action':'execute','code':code}));assert verification['pass'],verification
idle(probe(c));report=audit();assert report['pass'],report
files=snapshot();bound={p:files[p] for p in before}
write(D/'installed_repair_art_r02_20261029.json',{'recorded_at':now(),'parent_manifest_sha256':sha(D/'installed_manifest.json'),'art_revision':'art_r02','reason':'Head proportions found too small during first real-Play visual review; only final axial head dimensions/placement updated.','verification':verification,'changes':[{'path':p,'before':before[p],'after':s} for p,s in bound.items() if before[p]!=s],'protocol_history':c.history},True)
write(D/'preplay_version_binding_art_r02_20261029.json',{'recorded_at':now(),'art_revision':'art_r02','project':project,'production_fingerprints':bound,'all_production_fingerprints':files,'staged_fingerprints':{f.relative_to(D).as_posix():sha(f) for f in (D/'staged_art').iterdir() if f.is_file()},'manifest_sha256':sha(D/'installed_manifest.json'),'repair_manifest_sha256':sha(D/'installed_repair_art_r02_20261029.json'),'scope':report},True)
stage('art_r02_installed_verified_preplay_bound',D/'preplay_version_binding_art_r02_20261029.json')
print(json.dumps({'art_revision':'art_r02','verify':True,'scope_pass':report['pass'],'bound_files':len(bound)}))
