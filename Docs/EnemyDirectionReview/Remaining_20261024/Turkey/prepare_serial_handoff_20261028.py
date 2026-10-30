"""Seal the Turkey handoff and place the chain in handoff_ready."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = "01a18233-1a0c-7653-9ac2-6ecd99754a92"
TURKEY_TOKEN = "troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309"
NEXT_TOKEN = "turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c"
NEXT_NAME = "VolcanoParasite"
HANDOFF_REL = "Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261028_202757_Turkey_completed.md"
ASSESSMENT_REL = "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_assessment_20261028_202757.json"
PROMPT_REL = "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_prompt_20261028_202757.txt"
NEXT_REL = "Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


chain_path = H / "conversation_chain.json"
progress_path = H / "progress.json"
chain = read(chain_path)
assert chain["state"] == "active"
assert chain["owner_thread_id"] == OWNER and chain["dispatch_token"] == TURKEY_TOKEN
assert chain["current_character"] == "Turkey"
progress = read(progress_path)
turkey = next(row for row in progress["items"] if row["name"] == "Turkey")
next_item = next(row for row in progress["items"] if row["name"] == NEXT_NAME)
assert progress["completed_count"] == 90 and progress["current"] == NEXT_NAME
assert turkey["status"] == "completed_pending_user_art_review" and turkey["user_approved"] is False
assert next_item["index"] == 102 and next_item["status"] == "not_started"
assert (D / "final_validation_20261028.json").is_file()
assert (D / "scope_incremental_final_20261028.json").is_file()
assert (D / "version_binding_final_20261028.json").is_file()

responses = sorted(D.glob("unity_final_probe_20261028_response*.json"), key=lambda path: path.stat().st_mtime)
probe_path = next(path for path in reversed(responses) if read(path).get("success") is True)
probe = read(probe_path)
assert probe["project"]["projectRoot"].replace("\\", "/").lower() == "e:/mytowergame"
assert probe["project"]["unityVersion"] == "2022.3.62f3c1"
state = probe["results"][0]["data"]
errors = probe["results"][1]["structuredContent"]
live = probe["results"][2]["structuredContent"]["data"]["result"]
assert errors["success"] and errors["data"] == []
assert state["advice"]["ready_for_tools"] is True
assert state["activity"]["phase"] == "idle"
assert state["compilation"]["is_compiling"] is False
assert state["compilation"]["is_domain_reload_pending"] is False
assert state["assets"]["is_updating"] is False
assert state["tests"]["is_running"] is False
assert live["playing"] is False and live["compiling"] is False and live["failed"] is False
assert live["updating"] is False and live["review"] is False
assert live["scene"] == "Assets/Scenes/Boot.unity" and live["sceneDirty"] is False
assert live["sceneCount"] == 1
release = {
    "observed_at": probe["observed_at"],
    "released_by_thread_id": OWNER,
    "current_character": "Turkey",
    "next_character": NEXT_NAME,
    "next_dispatch_token": NEXT_TOKEN,
    "transport": probe["transport"],
    "project": probe["project"],
    "unity_instance": state["unity"]["instance_id"],
    "editor_state": state,
    "live_probe": live,
    "console_errors": errors["data"],
    "safe_to_handoff": True,
    "external_changes_dirty": state["assets"]["external_changes_dirty"],
    "note": "Unity is idle, Boot is the single clean scene, Play/review/tests are stopped, compilation and AssetDatabase updates are idle, and no console errors were returned. The editor reports external_changes_dirty=true while ready_for_tools=true; preserve and recheck this flag.",
    "probe_response_file": probe_path.name,
}
release_path = D / "handoff_release_20261028.json"
assert not release_path.exists()
write(release_path, release)

handoff = ROOT / HANDOFF_REL
assessment = ROOT / ASSESSMENT_REL
prompt = ROOT / PROMPT_REL
next_task = ROOT / NEXT_REL
assert all(path.is_file() for path in [handoff, assessment, prompt, next_task])
assert NEXT_TOKEN in prompt.read_text(encoding="utf-8")
assert NEXT_TOKEN in next_task.read_text(encoding="utf-8")

turkey["handoff_file"] = "conversation_handoffs/20261028_202757_Turkey_completed.md"
progress["current"] = NEXT_NAME
progress["updated_at"] = now()
write(progress_path, progress)

dispatch_path = H / NEXT_NAME / "prepared_dispatch_20261028.json"
assert not dispatch_path.exists()
dispatch = {
    "prepared_at": now(),
    "created": False,
    "parent_thread_id": OWNER,
    "character": NEXT_NAME,
    "character_index": 102,
    "dispatch_token": NEXT_TOKEN,
    "project_root": "E:/MyTowerGame",
    "project_id": chain["project_id"],
    "handoff_file": HANDOFF_REL,
    "handoff_sha256": sha(handoff),
    "assessment_file": ASSESSMENT_REL,
    "assessment_sha256": sha(assessment),
    "unity_release_file": "Docs/EnemyDirectionReview/Remaining_20261024/Turkey/handoff_release_20261028.json",
    "unity_release_sha256": sha(release_path),
    "prompt_file": PROMPT_REL,
    "prompt_sha256": sha(prompt),
    "next_task_file": NEXT_REL,
    "next_task_sha256": sha(next_task),
    "progress_sha256": sha(progress_path),
    "response_file": "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_creation_response_20261028.json",
    "project_association_confirmed": False,
}
write(dispatch_path, dispatch)

closed = chain.setdefault("completed_handoffs", [])
assert not any(row.get("character") == "Turkey" for row in closed)
closed.append({
    "character": "Turkey",
    "status": "completed_pending_user_art_review",
    "current_stage": "recorded_pending_user_art_review",
    "closed_at": now(),
    "owner_thread_id": OWNER,
    "dispatch_token": TURKEY_TOKEN,
    "handoff_file": HANDOFF_REL,
    "final_evidence": "Docs/EnemyDirectionReview/Remaining_20261024/Turkey/final_validation_20261028.json",
})
previous_handoff = chain.get("last_handoff_file")
chain.update(
    state="handoff_ready",
    parent_thread_id=OWNER,
    current_character=NEXT_NAME,
    character_status_at_handoff="not_started",
    owner_thread_id=OWNER,
    owner_host_id="local",
    dispatch_token=NEXT_TOKEN,
    completed_count_snapshot=90,
    previous_handoff_file=previous_handoff,
    last_handoff_file=HANDOFF_REL,
    handoff_sha256=sha(handoff),
    successor_assessment=ASSESSMENT_REL,
    prepared_dispatch_file="Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/prepared_dispatch_20261028.json",
    unity_release_file="Docs/EnemyDirectionReview/Remaining_20261024/Turkey/handoff_release_20261028.json",
    progress_sha256_at_handoff=sha(progress_path),
    handoff_ready_at=now(),
    updated_at=now(),
    successor_created=False,
    dispatch_ready_for=NEXT_NAME,
    current_stage="handoff_ready_reference_only",
    last_stage_evidence="Docs/EnemyDirectionReview/Remaining_20261024/Turkey/final_validation_20261028.json",
    resume_character=NEXT_NAME,
    resume_stage="Inspect current source anatomy/animations and establish a VolcanoParasite-specific incremental baseline",
    current_blocked=False,
    blocked_reason=None,
    stop_reason=None,
    stopped_at=None,
    ownership_transfer_note="Await one fresh local VolcanoParasite child. Until the child is registered active with this token, no thread may modify production assets or operate Unity.",
)
write(chain_path, chain)
print(json.dumps({
    "state": chain["state"],
    "next_character": NEXT_NAME,
    "token": NEXT_TOKEN,
    "completed_count": progress["completed_count"],
    "handoff_file": HANDOFF_REL,
    "unity_release_file": str(release_path),
    "prepared_dispatch_file": str(dispatch_path),
    "unity_external_changes_dirty": release["external_changes_dirty"],
}, ensure_ascii=False))
