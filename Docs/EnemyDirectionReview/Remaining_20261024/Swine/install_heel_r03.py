from session_swine import *
import shutil
owner();out=D/'local_raster_revision_03';assert not (out/'installation.json').exists()
manifest=read(D/'installed_manifest.json');assert all(sha(R/x['path'])==x['after'].upper() for x in manifest['changes'])
client=Client();project=client.identity();live=probe(client)
assert not any(v for k,v in live.items() if k!='scene'),live
art=R/'Assets/_UIAssets/Monsters/Pigs/Swine/Directions'
assert all(sha(art/('Swine_Directions'+s))==sha(D/'staged_art'/('Swine_Directions'+s)) for s in ['.sprites.json','.layout.json'])
clip=art/'Animations/Walk_Directions.anim';clip_before=sha(clip)
target=art/'Swine_Directions.png';before=sha(target);shutil.copy2(D/'staged_art/Swine_Directions.png',target)
refresh=client.tool('refresh_unity',dict(mode='force',scope='assets',compile='none',wait_for_ready=True));client.identity()
result=unwrap(client.tool('execute_code',dict(action='execute',code='FTProject.EditorTools.EnemyDirectionSpec spec;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("Swine",out spec);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);return new{pass=pass,report=report};')))
assert result['data']['result']['pass']
changes=[x for x in manifest['changes'] if sha(R/x['path'])!=x['after'].upper()]
assert len(changes)==1 and changes[0]['path']==target.relative_to(R).as_posix(),changes
assert sha(clip)==clip_before
changes[0]['after']=sha(target);manifest['verification']=result
manifest.setdefault('repair_history',[]).append(dict(observed_at=now(),revision=out.name,path=target.relative_to(R).as_posix(),before=before,after=sha(target),reason='Native rear heel faint triangle removed with full row interpolation; atlas-only replacement retains own Walk reset',prior_manifest=out.name+'/before_installed_manifest.json',no_full_build=True))
write(D/'installed_manifest.json',manifest);(D/'installed_verify.txt').write_text(result['data']['result']['report'],encoding='utf-8')
write(out/'installation.json',dict(observed_at=now(),project=project,viewed='staged_art/Up_LegFront.png at native size after r03 interpolation; smooth rear heel with outer outline retained',before=before,after=sha(target),walk_before=clip_before,walk_after=sha(clip),atlas_only=True,refresh=refresh,verify=result,history=client.history))
write(D/'preplay_version_binding_r02_20261028.json',dict(observed_at=now(),installed_manifest_sha256=sha(D/'installed_manifest.json'),installed_files={x['path']:sha(R/x['path']) for x in manifest['changes']},selection=read(D/'art_selection.json'),runtime_revisions=['runtime_r02','runtime_updeath_r02']))
c=owner();c.update(current_stage='heel_r03_installed_pending_two_Play_rounds',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Swine/local_raster_revision_03/installation.json',updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(installed='heel_r03',verify=True,atlas_only=True,walk_unchanged=True)))
