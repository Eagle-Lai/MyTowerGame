from serial_common import *
from PIL import Image,ImageDraw
import numpy as np
chain=owner();output=D/'incremental_before_20261026.json';assert not output.exists()
assert not (D/'installed_manifest.json').exists()
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
b=read(H/'production_fingerprints_before.json');protected=[t[k]+s for k in ['battle','source','atlas'] for s in ['', '.meta']]
assert all(sha(ROOT/p)==b[p] for p in protected)
assert not (ROOT/t['art_dir']).exists()
report=available(Client())
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
write(output,dict(observed_at=now(),files=files,protected_redscorpion={p:files[p] for p in protected},chain_owner=chain['owner_thread_id'],dispatch_token=chain['dispatch_token']))
write(D/'preinstall_identity_20261026.json',report)
write(D/'offline_review_20261026.json',dict(observed_at=now(),stage='offline_reviewed_pending_Unity',raster_revision='raster_revision_06',raw_sources_unchanged={k:sha(D/'generation'/k/'raw.png') for k in ['Up','Down']},targeted_torso_sha256=sha(D/'generation/Up/revision_01/raw.png'),final_staged={p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()},observations_zh='已实际查看原始图集、完整原始源prefab、两张原始生成图、定向躯干修复原图、切片板、透明细节和最终布局图。Up无脸后脑，去掉额外侧头刺；本地躯干补片过软、重绘过平均被否决，最终选用真实定向生成的三枚轴向背刺与连续圆拱甲片，按原设加宽。六步足、两钳、完整高拱尾按各自根连接，远足部分被身体与钳遮住；Down正面保留象牙眉角、琥珀眼和口钳，尾根在腹后，高拱完整在画面内。原始图片留盘不覆盖，所有局部修片留父版本和方法。透明孔洞是蝎尾拱口与张开的钳口，未画地面阴影。后续真实运行仍须检查连接、遮挡、死亡与血条关系。',user_approved=False))
print(json.dumps(dict(snapshot_files=len(files),protected_match=len(protected),project=report['project'],probe=report['probe']),ensure_ascii=False))
