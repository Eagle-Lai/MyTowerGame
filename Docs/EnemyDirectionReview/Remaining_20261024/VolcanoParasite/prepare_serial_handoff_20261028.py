"""Prepare a single fresh local Warg successor after the reviewed VolcanoParasite."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import re
import uuid

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = "01a18283-6ed7-71f0-97f7-6cc97bba20ff"
OLD_TOKEN = "turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c"
PROJECT_ID = "935c594c-f414-48e0-bd08-ed8ba342f7fd"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def now():
    return datetime.now(timezone(timedelta(hours=8)))


def relative(path):
    return path.relative_to(ROOT).as_posix()


chain_path = H / "conversation_chain.json"
progress_path = H / "progress.json"
chain = read(chain_path)
assert chain["state"] == "active" and chain["owner_thread_id"] == OWNER and chain["dispatch_token"] == OLD_TOKEN
assert chain["current_character"] == "VolcanoParasite"
progress = read(progress_path)
done = next(r for r in progress["items"] if r["name"] == "VolcanoParasite")
assert progress["completed_count"] == 91 and done["status"] == "completed_pending_user_art_review" and done["user_approved"] is False
remaining = [r for r in progress["items"] if r["status"] not in ["completed_pending_user_art_review", "user_approved"]]
recoverable = [r for r in remaining if r["status"] not in ["not_started", "blocked"]]
candidates = recoverable or [r for r in remaining if r["status"] != "blocked"]
selected = min(candidates, key=lambda r: r["index"])
assert selected["name"] == "Warg" and selected["index"] == 103 and selected["status"] == "not_started"
assert next(r for r in remaining if r["name"] == "PossessedWarg")["status"] == "blocked"
W = H / "Warg"
assert not (W / "prepared_dispatch_20261028.json").exists()
assert all(p.is_relative_to(W / "reference") for p in W.rglob("*") if p.is_file())
source = "Assets/_UIAssets/Monsters/Dogs/Warg/Warg.prefab"
atlas = "Assets/_UIAssets/Monsters/Dogs/Warg/Warg.png"
battle = "Assets/Prefabs/Enemy/Enemy_Warg.prefab"
protected = {p: sha(ROOT / p) for path in [battle, source, atlas] for p in [path, path + ".meta"]}
assert all(protected.values())
assert all(sha(W / "reference" / Path(p).name) == digest for p, digest in protected.items())
final_path = D / "final_validation_20261028.json"
final = read(final_path)
binding = read(D / "version_binding_final_20261028.json")
assert final["version_binding_sha256"] == sha(D / "version_binding_final_20261028.json")
assert final["incremental_scope_sha256"] == sha(D / "scope_incremental_final_20261028.json")
assert all(sha(ROOT / p) == digest for p, digest in binding["installed_files"].items())
assert (final["passes"], final["failures"], final["actual_png_frames"]) == (168, 0, 592)
probe_files = sorted(D.glob("unity_final_probe_20261028_response*.json"), key=lambda p: p.stat().st_mtime)
probe_path = next(p for p in reversed(probe_files) if read(p).get("success") is True)
probe = read(probe_path)
state = probe["results"][0]["data"]
live = probe["results"][2]["structuredContent"]["data"]["result"]
assert probe["project"]["projectRoot"].lower() == "e:/mytowergame" and probe["project"]["unityVersion"] == "2022.3.62f3c1"
assert probe["results"][1]["structuredContent"]["data"] == []
assert state["advice"]["ready_for_tools"] and state["activity"]["phase"] == "idle"
assert not state["tests"]["is_running"] and not state["compilation"]["is_domain_reload_pending"] and not state["assets"]["is_updating"]
assert all(live[k] is False for k in ["playing", "compiling", "failed", "updating", "sceneDirty", "balance", "recording", "review", "manual"])
assert live["scene"] == "Assets/Scenes/Boot.unity" and live["sceneCount"] == 1
stamp = now().strftime("%Y%m%d_%H%M%S")
token = "volcanoparasite-to-warg-20261028-" + str(uuid.uuid4())
handoff_path = H / "conversation_handoffs" / (stamp + "_VolcanoParasite_completed.md")
assessment_path = W / ("successor_assessment_" + stamp + ".json")
prompt_path = W / ("successor_prompt_" + stamp + ".txt")
release_path = D / "handoff_release_20261028.json"
assert all(not p.exists() for p in [handoff_path, assessment_path, prompt_path, release_path])
release = {"observed_at": probe["observed_at"], "released_by_thread_id": OWNER, "current_character": "VolcanoParasite",
           "next_character": "Warg", "next_dispatch_token": token, "transport": probe["transport"], "project": probe["project"],
           "unity_instance": state["unity"]["instance_id"], "editor_state": state, "live_probe": live, "console_errors": [],
           "safe_to_handoff": True, "external_changes_dirty": state["assets"]["external_changes_dirty"],
           "probe_response_file": probe_path.name, "probe_response_sha256": sha(probe_path),
           "note": "Boot is the single clean scene; Play, tests, review, balance, recording, manual simulation, compilation and updates are idle. No console errors."}
write(release_path, release)
assessment = {"observed_at": now().isoformat(), "completed_count": 91, "authorized_count": 108,
              "selection": "Recover started nonblocked roles first, otherwise lowest incomplete nonblocked index.",
              "remaining": [{"index": r["index"], "name": r["name"], "status": r["status"]} for r in remaining],
              "next_character": "Warg", "next_index": 103, "status": "not_started", "dispatch_token": token,
              "protected_six": protected, "reference_matches_live": True,
              "existing_files": [p.relative_to(W).as_posix() for p in sorted(W.rglob("*")) if p.is_file()],
              "no_generation_staging_install_or_runtime": True, "blocked_preserved": [r for r in remaining if r["status"] == "blocked"],
              "project_id": PROJECT_ID, "project_id_source": "Current list_projects result confirmed E:/MyTowerGame on local host before handoff preparation."}
write(assessment_path, assessment)
handoff = f"""# VolcanoParasite(index 102) 完成与 Warg(index 103) 串行交接

时间：{now().isoformat()}。父线程 `{OWNER}`，旧 token `{OLD_TOKEN}`。当前技术状态 `completed_pending_user_art_review`，`user_approved=false`，进度 **91/108**。下一唯一角色 Warg，不处理其他角色。

## 最终版本与实际修改

无眼、无足、无翼的金赭色分节寄生虫，深棕弯背角，Down保留上下两排象牙牙齿和浅金下颚，Up为无脸无牙后视。共12张透明分件，每向6张，四段连接爬行。Up选择 `generation/Up/raw.png`，Down选择 `generation/Down/revision_01/raw.png`；三次正式请求均HTTP200，Down初稿缺下排牙已否决，原请求与raw保留。本地分件派生修正重复体节，仅填补11个封闭alpha像素，最终分件内部透明孔和不透明magenta均0。

R01两轮技术通过但Up/Down体量偏小，已否决。R02仅分件width/height放大2.1倍，pivot/center/phase/根缩放和业务数值保留；两轮技术通过但发现死亡复用后Left/Right倒置，已否决。R03只给本角色专用Ready/Walk动画添加Body/localEulerAnglesRaw.x/y/z常量0曲线，清除原Death遗留旋转；不改共享C#、源图集、共享动画或其他角色。原曲线、事件、时长、loop通过Verify；Death原事件为 `SetHead(1)` at0，Attack为 `Event(\"Attack\")` at约0.3666667，不能套用其他寄生虫事件。

最终指纹由 `repair_proportions_r02/manifest.json` 的**全量21路径**加 `repair_pool_rotation_r03/manifest.json` 的2动画覆盖组成。仅检查R03的2项是不完整的；不要重跑Build覆盖R03修复。精确指纹见 `VolcanoParasite/version_binding_final_20261028.json`：

- battle prefab：`{binding['installed_files']['Assets/Prefabs/Enemy/Enemy_VolcanoParasite.prefab']}`
- Ready：`{binding['installed_files']['Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/Directions/Animations/Ready_Directions.anim']}`
- Walk：`{binding['installed_files']['Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/Directions/Animations/Walk_Directions.anim']}`

## 最终运行、视觉与归档

`runtime_r03` 与 `runtime_updeath_r03` 各84 PASS /0 FAIL、296帧，合计168/0、592张真实Unity PNG。两轮均回Boot；第二轮Up死亡。记录SHA分别为 `{final['runtime'][0]['records_sha256']}` 和 `{final['runtime'][1]['records_sha256']}`。

实际查看：无裁切离线解剖图、两轮四向图、runtime strip、全部10张时序/步态/愤怒板、8张选定原尺寸PNG，以及最终12个GIF各5个编码帧样本共60。观察到体节相连、头躯错相、攻击前压、受击白闪恢复、两向死亡侧倾缩小淡出、对象池复用恢复及暂停倍速继续。R03复用后左右转向背角朝上，R02倒置不再出现。GIF为编码帧抽样，**非实时播放、非逐GIF全帧审核**。顺序板crop会裁顶部角，原PNG及无裁切proof可区分；原HP条在部分水平姿态覆盖角尖，未改其位置。用户美术仍待验收。

record已完成。AllGIF实为1474项，本角色36项源/归档SHA全匹配，其中R03最终12项为当前审核版本，R01/R02的24项为历史材料。详细证据：

- `VolcanoParasite/final_validation_20261028.json`
- `VolcanoParasite/version_binding_final_20261028.json`
- `VolcanoParasite/scope_incremental_final_20261028.json`
- `VolcanoParasite/visual_review_r03_20261028/review.json`
- `VolcanoParasite/gif_archive_verification_20261028.json`
- `VolcanoParasite/record_note_utf8.txt`

## 增量范围与Unity释放

5365文件安装前快照与当前5385文件作路径并集，22路径变化、20新增；仅本角色battle prefab及Directions含meta，另有未修改ReporterEditor写入build_info时间戳，unexpected_incremental=0。本角色prefab语义检查通过，根/HP/碰撞/参数等保留；六保护除允许battle改动外其余5项不漂移，共享C#无漂移，staged三文件与production SHA一致。旧全局审计291项unexpected和6个其他角色历史语义失败仍单列，不能宣称全局PASS。

Unity由8088动态custom-tools/instances选当前MyTowerGame并核对E:/MyTowerGame /2022.3.62f3c1。最后释放为Boot单场景、非Play、全部场景clean、编译/更新/域重载/test/review/balance/recording/manual均idle，scriptCompilationFailed=false、console error0、ready_for_tools=true、external_changes_dirty={str(state['assets']['external_changes_dirty']).lower()}。证据 `{relative(release_path)}`。本聊天用户已明确允许结束初始Main Play并交给任务验证，已执行；不得据此强停后续其他任务。桌面操作仍需单独确认，本轮未用桌面控制。

## 下一唯一Warg

实时队列17项未完成；只有PossessedWarg旧blocked/uncertain，原记录保留且不自动重发。其余候选按index，Warg103 not_started；只存在reference，没有生成请求/原图/暂存/安装/运行。源prefab `{source}`，atlas `{atlas}`，battle `{battle}`；六保护与reference匹配。不要从别的狼兽照搬具体造型，下一聊天自行完整审图、动画/事件、行为和生命周期，建立Warg专属基线。评估 `{relative(assessment_path)}`。

新唯一dispatch token：`{token}`。完整执行入口 `{relative(prompt_path)}` 与 `NEXT_ENEMY_TASK.md`。链为handoff_ready时任何线程不改生产；create明确成功并登记新线程active后，只有新owner继续，本父线程停止工程写入。创建唯一fresh local后继，禁止fork、子代理、定时器、并行角色、模型或推理覆盖。按协议循环到全部有效完成或只剩真实阻断，不等待逐角色确认。
"""
handoff_path.write_text(handoff, encoding="utf-8")
prompt = f"""在 E:/MyTowerGame 继续敌人四方向串行续作。本聊天唯一角色为 Warg(index 103)。这是用户已明确授权的唯一全新 local 后继，不是并行任务。

唯一 dispatch token：{token}
父线程：{OWNER}

开工先读取以下完整文件，核对当前磁盘、未提交改动、所有权与唯一角色：
1. E:/MyTowerGame/AGENTS.md 与 ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录 CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录 standing_network_recovery_authorization_20261028.json 与 TreasureChest/standing_recovery_application_20261028.json。既有同类网络失败静默有界恢复授权须核对原证据，不改写旧uncertain/收费结果，不无限请求。
6. E:/MyTowerGame/{relative(handoff_path)}。
7. E:/MyTowerGame/{relative(assessment_path)}。
8. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/Warg/reference/source_structure.json 及该目录完整源参考。

父会先将chain准备成handoff_ready。只有实时chain.state=active、owner_thread_id为本新线程、current_character=Warg、dispatch_token与上方完全匹配后，才可操作Unity、生产资产或付费图片请求。handoff_ready期间只读等待登记，不能超时抢锁。创建成功后父线程停止所有工作区写入。

当前进度91/108，VolcanoParasite102已record、completed_pending_user_art_review、user_approved=false。Warg103为not_started，只有reference，没有anatomy/generation/raw/staged/install/runtime。父新增的assessment/prompt/dispatch属于调度文档，不代表已开始美术生产。只处理Warg，恢复时先检查新出现的材料，避免重复prepare、付费生成或安装。

Warg当前源路径：
- Assets/Prefabs/Enemy/Enemy_Warg.prefab
- Assets/_UIAssets/Monsters/Dogs/Warg/Warg.prefab
- Assets/_UIAssets/Monsters/Dogs/Warg/Warg.png
metadata及reference已匹配，仍由本线程开工实时核对。检查完整图集、prefab层级、Controller依赖、原事件/曲线/时长与loop、战斗行为及对象池生命周期；自行制定Warg解剖、足尖朝向、尾根遮挡和步态，不能照搬其他狼兽。改动前建立Warg专属Assets/Packages/ProjectSettings/Luban全部路径SHA基线及六保护指纹，保留用户已有修改，不以Git HEAD作本轮基线。

严格执行原prompt逐阶段流程：审原图与解剖→需要时逐方向AIHub生成并实看raw→透明分件/pivot/layout与离线proof审阅→仅本角色安装及Verify→两轮真实Unity Play各84项→分批实看原PNG/时序板/GIF并准确记录抽样范围→UTF-8 note/record→GIF集中归档与源/归档SHA核对→最终版本绑定和路径并集增量审计。已有请求必须先检查结果，成功raw复用、拒绝稿保留、不确定不盲重发。图像服务按任务gpt-image-2/medium/1536x1024/n1和AIHub运行时密钥规则，不泄露密钥或图片base64。

最终status只能completed_pending_user_art_review、user_approved=false。技术通过不能冒充美术批准；视觉失败即使168/0也必须返修。保留源图集、侧向原曲线/PPtr/事件/时长/loop、root/GUID、HP、碰撞/锚点、业务数值，方向采用现有系统。不改配置表、Assets/ConfigJson、Assets/Gen、声音、其他角色或共享C#；若真有共享缺陷必须先明确依赖及最小范围并遵守原prompt编译回归规则，不擅自扩大。

正确现场为E:/MyTowerGame、Unity2022.3.62f3c1、http://127.0.0.1:8088/mcp。复用Remaining_20261024/mcp_call.py，每次动态读custom-tools/instances、明确set现场MyTowerGame完整ID、project/info核路径和版本。8082当前其他工程、8080 CatchFish；根AGENTS的FreedomTower/D盘/8082属于历史错配，不覆盖本任务。新连接/域重载后重核身份。默认Unity MCP，电脑/桌面控制仍要先弹对话确认，勿擅用。只停本任务授权的测试Play，不强停外来任务。父释放时Boot单场景clean、非Play、全部测试/编译/重载/更新/录像/手工模拟idle、scriptCompilationFailed=false、error0、ready_for_tools=true、external_changes_dirty={str(state['assets']['external_changes_dirty']).lower()}；现场变化时先核对。C#如有改动必须正确MCP refresh/compile/state/error闭环，期间不继续改代码，不清日志。

VolcanoParasite最终R03：runtime_r03/runtime_updeath_r03各84/0、296帧，共168/0和592 PNG；实审10时序/步态/愤怒板、8张原尺寸PNG、四向/strip/无裁切proof、12GIF各5个编码帧样本。R01体量不足、R02死亡复用侧身倒置均否决保留，R03专用Ready/Walk加Body角度清零修复。其最终21路径指纹是R02全量manifest加R03两动画覆盖，不能仅检查两项、重Build或重装掉修复。AllGIF1474，本角色36含最终12，其余24历史，SHA匹配。5365→5385文件并集22变化、增量unexpected0、本角色语义/源保护/共享C#无漂移；未改Reporter写build_info单列。旧全局291unexpected/6其他角色历史语义失败不冒称全局通过。前任最终证据在VolcanoParasite/final_validation_20261028.json及其version_binding/scope/visual_review/gif_archive文件，不应重复执行前任。

PossessedWarg旧blocked/uncertain保留，不自动重发、不伪称完成。禁止Git pull/reset/clean/commit、构建部署、fork、子代理、并行角色、计时器和模型/推理覆盖。不要更新用户长期memory。

用户已授权“一个角色完成→完整总结→更新prompt/NEXT→创建唯一全新local后继”的串行循环，无需逐角色再确认。完成Warg全部验收或记录真实阻断后重评实时队列，优先可恢复已开始项，否则按index选择下一非blocked；完整交接、更新README/原prompt实时块/NEXT/progress、释放Unity，按协议list_projects确认E:/MyTowerGame项目ID并只create_thread一个fresh local项目聊天，不传model/thinking、不fork。先handoff_ready，新聊天等待；创建明确成功后保存实际响应并登记新owner/token active作为父线程最终写入，随后停止工作区修改，做一次有界wait_threads并报告真实created-thread ID。若创建结果不明先查列表，不盲重试；工具失败保留可执行交接并如实报告。循环到全部有效完成或只剩真实阻断。
"""
prompt_path.write_text(prompt, encoding="utf-8")
(H / "NEXT_ENEMY_TASK.md").write_text("# 下一唯一角色 Warg(index 103)\n\n" + prompt, encoding="utf-8")
live_text = (f"2026-10-28 VolcanoParasite102已record，91/108，completed_pending_user_art_review、user_approved=false。最终R03，12透明分件、11封闭alpha像素修补。"
             f"R01体量不足和R02复用倒置已否决保留；R03仅专用Ready/Walk加Body角度清零曲线，原事件/曲线/时长/loop及root/HP/pool Verify通过，无共享C#改动。"
             f"runtime_r03与runtime_updeath_r03各84/0、296帧，合计168/0与592真实PNG。实审四向/strip、10时序/步态/愤怒板、8原尺寸PNG、无裁切proof、12GIF各5编码帧抽样；非实时播放或逐GIF全帧审核。"
             f"Up无脸无牙、Down上下两排牙，四段无足爬行，复用后左右背角朝上。AllGIF1474，本角色36含12当前/24历史，全部源归档SHA匹配。"
             f"5365→5385文件并集22变化20新增，incremental unexpected0、本角色语义通过、其余5保护/共享C#无漂移；Reporter未改代码写build_info单列。旧global291unexpected/6历史语义失败不属于本角色增量，未称全局PASS。"
             f"Unity8088动态核E:/MyTowerGame/2022.3.62f3c1，Boot单场景clean、非Play、全部编译/更新/测试/录像/模拟idle、failed=false/error0/ready=true，external_changes_dirty={str(state['assets']['external_changes_dirty']).lower()}。"
             f"最终证据VolcanoParasite/final_validation_20261028.json及version_binding/scope/visual_review/gif_archive。交接{relative(handoff_path)}。"
             f"下一唯一Warg103 not_started，token={token}；PossessedWarg旧blocked/uncertain保留。")
for path, begin, end in [(H.parent / "README.md", "<!-- ENEMY_README_LIVE_BEGIN -->", "<!-- ENEMY_README_LIVE_END -->"),
                          (H / "REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md", "<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->", "<!-- ENEMY_SERIAL_LIVE_STATE_END -->")]:
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.escape(begin) + r".*?" + re.escape(end)
    assert len(re.findall(pattern, text, re.S)) == 1
    text = re.sub(pattern, lambda _: begin + "\n" + live_text + "\n" + end, text, flags=re.S)
    path.write_text(text, encoding="utf-8")
done["handoff_file"] = handoff_path.relative_to(H).as_posix()
progress.update(current="Warg", updated_at=now().isoformat())
write(progress_path, progress)
dispatch_path = W / "prepared_dispatch_20261028.json"
dispatch = {"prepared_at": now().isoformat(), "created": False, "parent_thread_id": OWNER, "character": "Warg", "character_index": 103,
            "dispatch_token": token, "project_root": "E:/MyTowerGame", "project_id": PROJECT_ID,
            "handoff_file": relative(handoff_path), "handoff_sha256": sha(handoff_path),
            "assessment_file": relative(assessment_path), "assessment_sha256": sha(assessment_path),
            "unity_release_file": relative(release_path), "unity_release_sha256": sha(release_path),
            "prompt_file": relative(prompt_path), "prompt_sha256": sha(prompt_path),
            "next_task_file": relative(H / "NEXT_ENEMY_TASK.md"), "next_task_sha256": sha(H / "NEXT_ENEMY_TASK.md"),
            "progress_sha256": sha(progress_path), "response_file": relative(W / "successor_creation_response_20261028.json"),
            "project_association_confirmed": False}
write(dispatch_path, dispatch)
closed = chain.setdefault("completed_handoffs", [])
assert not any(r.get("character") == "VolcanoParasite" for r in closed)
closed.append({"character": "VolcanoParasite", "status": "completed_pending_user_art_review", "current_stage": "recorded_pending_user_art_review",
               "closed_at": now().isoformat(), "owner_thread_id": OWNER, "dispatch_token": OLD_TOKEN,
               "handoff_file": relative(handoff_path), "final_evidence": relative(final_path)})
chain.update(state="handoff_ready", parent_thread_id=OWNER, owner_thread_id=OWNER, owner_host_id="local", current_character="Warg",
             dispatch_token=token, character_status_at_handoff="not_started", completed_count_snapshot=91,
             previous_handoff_file=chain.get("last_handoff_file"), last_handoff_file=relative(handoff_path), handoff_sha256=sha(handoff_path),
             successor_assessment=relative(assessment_path), prepared_dispatch_file=relative(dispatch_path), unity_release_file=relative(release_path),
             progress_sha256_at_handoff=sha(progress_path), handoff_ready_at=now().isoformat(), updated_at=now().isoformat(),
             successor_created=False, dispatch_ready_for="Warg", current_stage="handoff_ready_reference_only", last_stage_evidence=relative(final_path),
             resume_character="Warg", resume_stage="Inspect Warg anatomy/animations and establish its own incremental baseline", current_blocked=False,
             blocked_reason=None, stop_reason=None, stopped_at=None,
             ownership_transfer_note="Await one fresh local Warg child; no production/Unity work until successful creation is registered active.")
write(chain_path, chain)
print(json.dumps({"state": chain["state"], "next_character": "Warg", "token": token, "completed_count": 91,
                  "handoff_file": relative(handoff_path), "prompt_file": relative(prompt_path), "prepared_dispatch_file": relative(dispatch_path)}, ensure_ascii=False))
