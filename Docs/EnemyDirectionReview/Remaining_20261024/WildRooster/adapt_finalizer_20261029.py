"""Adapt proven evidence machinery, confined to WildRooster documentation."""
from pathlib import Path

D=Path(__file__).resolve().parent
p=D/'finalize_wildrooster_20261029.py'
assert not p.exists()
s=(D.parent/'WildGoat/finalize_wildgoat_20261029.py').read_text(encoding='utf-8')
def replace(a,b):
    global s
    assert a in s,a
    s=s.replace(a,b)
replace('WildGoat','WildRooster')
replace('01a1841b-d4fc-7eb2-9ace-b66dc688e0c2','01a18560-5f4b-7b42-a2cf-f926c68a77ae')
replace('whitewolf-to-wildgoat-20261029_040116-747154f6-09f2-4b00-940c-121c7a063e19','wildgoat-to-wildrooster-20261029_095556-9aeda72a-08aa-4bfe-aca0-1b03c0381c5e')
replace('runtime_updeath_r02','runtime_updeath_r01')
replace('runtime_r02','runtime_r01')
replace('art_r02','art_r03')
replace('local_raster_r02','local_raster_r03')
replace('5465','5485')
replace('596','600')
replace("manifest_path = D / 'repair_art_r03/manifest.json'","manifest_path = D / 'installed_manifest.json'")
replace("D / 'repair_art_r03/verify.txt'","D / 'installed_verify.txt'")
replace("len(installation['changes']) == 21","len(installation['changes']) == 20")
replace("assert repair['revision'] == REVISION and repair['raw_unchanged']","assert repair['revision'] == REVISION")
replace("repair['raw_sha256']","repair['raws']")
replace("repair['staged_inputs']","repair['files']")
replace("assert im.size == (s['w'], s['h']) and im.getchannel('A').getbbox()", "assert im.size == (s['w'], s['h'])\n+    if s['name'].endswith('_Tail'):\n+        assert im.size == (1,1) and im.getchannel('A').getbbox() is None\n+    else:\n+        assert im.getchannel('A').getbbox()")
replace("snapshot['observed_at']","snapshot['at']")
replace("installation['at']","installation['installed_at']")
replace("reviewed = ['offline_rig_proof.png','parts_clean.png','runtime_visual_strip.png']", "reviewed = ['offline_rig_proof.png','local_raster_r03/body_review.png','runtime_visual_strip.png']")
start=s.index("originals = ['runtime_r01/frames/'")
end=s.index('visual = {',start)
note='最终art_r03实际查看最终离线rig/局部Body、两轮四向图和runtime strip、10张时序/步态/愤怒细节板（{positions}采样位、{unique}张不同真实PNG）、6张768像素完整原PNG、12个最终GIF各5个编码帧共60帧，另看两轮Up/Down各1张未裁切GIF编码整帧。原金赭公鸡的高金冠、奶油长脸/后颈、钩形金喙与双瓣垂肉、白根金羽双翅、双金爪及Body一体尾羽身份保留。离线r01因浮翅/重复领口/高位尾簇否决，r02因帽盖接缝和矩形尾根否决，历史保留；r03局部RGBA清理和混色，Up三羽尾簇融合到下臀，Down正面尾羽被躯干遮蔽、移除重复领口/突起，双翼内收、头身重叠和腿根内收。原Up/Down成功raw未改，两方向各一次HTTP200，无重试/新增付费请求；usage估算不是实际账单。Up纯后脑无脸，三表情同图；Down正常/愤怒/死亡头保留。原左右侧面保留，头颈/肩/腿根相连，实际每方向双翅双腿且无Tail节点，透明1x1 Tail仅兼容切片，无地面阴影。步态错相、攻击头切换、受击白闪及恢复、Down/Up死亡旋转缩小淡出、自动回收、同实例正常Down复用、暂停冻结/恢复和1x/2x/3x推进均有运行记录与时序抽样。部分通用板裁切了冠尖，原始整帧和未裁切GIF帧确认完整、血条有间距。GIF为编码帧抽样，非实时播放或逐GIF全帧审阅；600张原PNG均保留并哈希绑定。内部技术视觉通过，用户美术验收待进行。'
s=s[:start]+"originals = ['runtime_r01/frames/UpWalk_00004.png','runtime_r01/frames/DownWalk_00023.png','runtime_r01/frames/Attack_00122.png','runtime_updeath_r01/frames/DeathAutoRecycle_00144.png','runtime_updeath_r01/frames/Reuse_00154.png','runtime_updeath_r01/frames/LeftWalk_00039.png']\nnote = f"+repr(note)+"\n"+s[end:]
replace("'rejected_revision':'local_raster_r03/rejected_r01_visual.json'", "'rejected_revisions':['offline_r01','offline_r02'],'offline_review_file':'offline_review_art_r03_20261029.json'")
replace("D/'unity_release_post_r02_20261029.json'","D/'unity_release_final_r03_20261029.json'")
replace("'unity_release_post_r02_20261029.json'","'unity_release_final_r03_20261029.json'")
replace("assert len(rows)==24","assert len(rows)==12")
replace("'historical_gifs':12","'historical_gifs':0")
replace("progress['completed_count']==96","progress['completed_count']==97")
replace("selected['name']=='WildRooster' and selected['index']==108","selected['name']=='WinterBear' and selected['index']==109")
replace("'manifest':'repair_art_r03/manifest.json'","'manifest':'installed_manifest.json'")
replace("All 22 prePlay production paths unchanged; final r02 installed before both runs; old r01 preserved and rejected.","All 22 prePlay production paths unchanged; final art_r03 installed once before both runtime_r01 runs; rejected offline r01/r02 preserved.")
replace("'archived_character_gifs':24","'archived_character_gifs':12")
replace("'completed_count':96","'completed_count':97")
replace("'archived_gifs':24","'archived_gifs':12")
replace("write(D/'scope_incremental_final_20261029.json',scope)","assert (len(before),len(current),len(changes),sum(r['before'] is None for r in changes))==(5485,5505,22,20)\n+    write(D/'scope_incremental_final_20261029.json',scope)")
s=s.replace('\n+','\n')
p.write_text(s,encoding='utf-8')
print(p)
