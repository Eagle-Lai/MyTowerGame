from serial_common import *
chain=owner();output=D/'incremental_before_20261026.json';assert not output.exists()
assert not (D/'installed_manifest.json').exists()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
b=read(H/'production_fingerprints_before.json');protected=[t[k]+s for k in ['battle','source','atlas'] for s in ['', '.meta']]
assert all(sha(ROOT/p)==b[p] for p in protected)
for k in ['battle','source','atlas']:
    for suffix in ['', '.meta']:assert sha(D/'reference'/(Path(t[k]).name+suffix))==b[t[k]+suffix]
report=available(Client());assert report['errors']['data']==[]
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
write(output,dict(observed_at=now(),files=files,protected_rooster={p:files[p] for p in protected},chain_owner=chain['owner_thread_id'],dispatch_token=chain['dispatch_token']))
write(D/'preinstall_identity_20261026.json',report)
write(D/'offline_review_20261026.json',dict(observed_at=now(),stage='offline_reviewed_pending_Unity',raster_revision='raster_revision_02',layout_revision='offline_final_after_revision_03',raw_sources_unchanged={k:sha(D/'generation'/k/'raw.png') for k in ['Up','Down']},final_staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},
    observations_zh='已实际查看原始生成和源参考(前段)、当前完整分件板、Up/Down离线整身及Up脚原尺寸。初始漂浮翅膀、重复颈段与倒置脚趾被拒并归档。最终翅根收拢到躯干肩部，Up头层位22覆盖Body颈帽，Down颈部加长稍向左与原颈插口重叠。Up脚保留原金色杆/奶油羽毛袖，局部修成金色后跟和单后趾，无三趾朝向观察者。未新增原prefab未绑定的金尾，白色尾臀轮廓在Body内；兼容Tail透明且节点删除。正面保留眼/嘴/垂肉，背面无脸；当前图未见紫边、误抠孔洞或地面阴影。真实运行尚须审接缝、死亡与血条关系。',user_approved=False))
print(json.dumps(dict(snapshot_files=len(files),protected_match=len(protected),project=report['project'],probe=report['probe']),ensure_ascii=False))
