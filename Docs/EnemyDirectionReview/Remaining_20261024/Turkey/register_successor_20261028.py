"""Record the successful VolcanoParasite thread dispatch and transfer ownership."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = "01a18233-1a0c-7653-9ac2-6ecd99754a92"
THREAD_ID = "01a18283-6ed7-71f0-97f7-6cc97bba20ff"
HOST_ID = "local"
NEXT_NAME = "VolcanoParasite"
TOKEN = "turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c"
HANDOFF = "Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261028_202757_Turkey_completed.md"
PROMPT = "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_prompt_20261028_202757.txt"
ASSESSMENT = "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_assessment_20261028_202757.json"
RESPONSE = "Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_creation_response_20261028.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


chain_path = H / "conversation_chain.json"
dispatch_path = H / NEXT_NAME / "prepared_dispatch_20261028.json"
response_path = ROOT / RESPONSE
chain = read(chain_path)
dispatch = read(dispatch_path)
assert chain["state"] == "handoff_ready"
assert chain["parent_thread_id"] == OWNER
assert chain["owner_thread_id"] == OWNER
assert chain["current_character"] == NEXT_NAME and chain["dispatch_token"] == TOKEN
assert dispatch["created"] is False and dispatch["dispatch_token"] == TOKEN
assert dispatch["project_id"] == "935c594c-f414-48e0-bd08-ed8ba342f7fd"
assert dispatch["prompt_sha256"] == sha(ROOT / PROMPT)
assert dispatch["handoff_sha256"] == sha(ROOT / HANDOFF)
assert not response_path.exists()
assert not any(entry.get("dispatch_token") == TOKEN for entry in chain.get("dispatch_history", []))

recorded_at = now()
response = {
    "recorded_at": recorded_at,
    "tool": "mcp__codex_app__create_thread",
    "created": True,
    "thread_id": THREAD_ID,
    "host_id": HOST_ID,
    "project_id": dispatch["project_id"],
    "project_path": "E:/MyTowerGame",
    "project_association_confirmed": True,
    "title": "Enemy Directions: VolcanoParasite",
    "prompt_file": PROMPT,
    "prompt_sha256": sha(ROOT / PROMPT),
    "handoff_file": HANDOFF,
    "dispatch_token": TOKEN,
    "tool_result": {"threadId": THREAD_ID, "hostId": HOST_ID},
}
write(response_path, response)

dispatch.update(
    created=True,
    created_at=recorded_at,
    thread_id=THREAD_ID,
    host_id=HOST_ID,
    project_association_confirmed=True,
    response_file=RESPONSE,
    response_sha256=sha(response_path),
)
write(dispatch_path, dispatch)

history = chain.setdefault("dispatch_history", [])
sequence = max((entry.get("sequence", 0) for entry in history), default=0) + 1
history.append({
    "sequence": sequence,
    "character": NEXT_NAME,
    "thread_id": THREAD_ID,
    "host_id": HOST_ID,
    "dispatch_token": TOKEN,
    "created": True,
    "project_association_confirmed": True,
    "project_id": dispatch["project_id"],
    "handoff_file": HANDOFF,
    "successor_prompt_file": PROMPT,
    "creation_response_file": RESPONSE,
    "created_at": recorded_at,
})
chain.update(
    state="active",
    parent_thread_id=OWNER,
    owner_thread_id=THREAD_ID,
    owner_host_id=HOST_ID,
    current_character=NEXT_NAME,
    dispatch_token=TOKEN,
    character_status_at_handoff="not_started",
    completed_count_snapshot=90,
    last_handoff_file=HANDOFF,
    handoff_sha256=sha(ROOT / HANDOFF),
    prepared_dispatch_file="Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/prepared_dispatch_20261028.json",
    creation_response_file=RESPONSE,
    successor_created=True,
    dispatch_ready_for=None,
    current_stage="not_started_owner_registered",
    last_stage_evidence=ASSESSMENT,
    resume_character=NEXT_NAME,
    resume_stage="Verify active ownership token, inspect current source, and establish the incremental baseline",
    current_blocked=False,
    blocked_reason=None,
    stop_reason=None,
    stopped_at=None,
    ownership_transfer_note="Fresh local VolcanoParasite thread confirmed and registered. The child owns all subsequent production and Unity work; parent must not mutate the workspace.",
    updated_at=recorded_at,
)
write(chain_path, chain)
print(json.dumps({
    "state": chain["state"],
    "thread_id": THREAD_ID,
    "host_id": HOST_ID,
    "character": NEXT_NAME,
    "dispatch_token": TOKEN,
    "sequence": sequence,
    "project_association_confirmed": True,
    "response_file": RESPONSE,
}, ensure_ascii=False))
