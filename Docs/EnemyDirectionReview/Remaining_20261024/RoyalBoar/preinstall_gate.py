from serial_common import *
chain=owner();output=D/'incremental_before_20261026.json';assert not output.exists()
assert not (D/'installed_manifest.json').exists()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
b=read(H/'production_fingerprints_before.json');protected=[t[k]+s for k in ['battle','source','atlas'] for s in ['', '.meta']]
assert all(sha(ROOT/p)==b[p] for p in protected)
for k in ['battle','source','atlas']:
    for suffix in ['', '.meta']:assert sha(D/'reference'/(Path(t[k]).name+suffix))==b[t[k]+suffix]
report=available(Client());assert report['errors']['success'] and report['errors']['data']==[]
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
write(output,dict(observed_at=now(),files=files,protected_royalboar={p:files[p] for p in protected},chain_owner=chain['owner_thread_id'],dispatch_token=chain['dispatch_token']))
write(D/'preinstall_identity_20261026.json',report)
write(D/'offline_review_20261026.json',dict(observed_at=now(),stage='offline_reviewed_pending_Unity',raster_revision='raster_revision_02',layout_revision='offline_final_after_revision_04',raw_sources={str(p.relative_to(D)):sha(p) for p in (D/'generation').rglob('raw.png')},final_staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},
    observations_zh='实际查看源图集及完整战斗prefab，原始Up/Down与Up revision01，全部分件和四次离线布局。最初躯干重复脸/鬃毛被拒。Down两次修订明确503，保留原记录；仅将已生成干净金斑躯干拼入Down，保留原三表情和腿。本地修掉Up后脑象牙色小片/内线及脚尖分缝，保留描边和透明轮廓，原付费图未改。Down Dead右轮廓已补全；躯干无脸无鬃毛，Up后脑无五官。四足根嵌入圆躯干，远足仅露下侧小蹄，近足短粗；曾外露圆髋的布局已归档拒绝。原六renderer无独立Tail，因此透明兼容slice且删除两个Tail节点。未见紫边/孔洞/地面阴影；当前离线图已可安装，真实运行仍需审步态接缝、表情与死亡。',user_approved=False))
print(json.dumps(dict(snapshot_files=len(files),protected_match=len(protected),project=report['project'],probe=report['probe']),ensure_ascii=False))
