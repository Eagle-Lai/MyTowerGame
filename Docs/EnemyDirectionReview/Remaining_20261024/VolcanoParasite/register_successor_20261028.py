"""Register the actual, already-created Warg child; transfer ownership last."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = "01a18283-6ed7-71f0-97f7-6cc97bba20ff"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


dispatch_path = H / "Warg/prepared_dispatch_20261028.json"
dispatch = read(dispatch_path)
chain_path = H / "conversation_chain.json"
chain = read(chain_path)
thread_id, host_id = sys.argv[1:3]
response_path = ROOT / dispatch["response_file"]
raw = read(response_path)
assert raw.get("isError") is not True
result = raw.get("structuredContent")
if not result:
    result = next(json.loads(x["text"]) for x in raw["content"] if x.get("type") == "text")
assert result["threadId"] == thread_id and result["hostId"] == host_id
assert chain["state"] == "handoff_ready" and chain["owner_thread_id"] == OWNER
assert chain["parent_thread_id"] == OWNER and chain["current_character"] == "Warg"
assert chain["dispatch_token"] == dispatch["dispatch_token"] and dispatch["created"] is False
assert sha(ROOT / dispatch["prompt_file"]) == dispatch["prompt_sha256"]
assert sha(ROOT / dispatch["handoff_file"]) == dispatch["handoff_sha256"]
assert not any(r.get("dispatch_token") == dispatch["dispatch_token"] for r in chain.get("dispatch_history", []))
stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
dispatch.update(created=True, created_at=stamp, thread_id=thread_id, host_id=host_id,
                response_sha256=sha(response_path), project_association_confirmed=True)
write(dispatch_path, dispatch)
history = chain.setdefault("dispatch_history", [])
sequence = max((r.get("sequence", 0) for r in history), default=0) + 1
history.append({"sequence": sequence, "character": "Warg", "thread_id": thread_id, "host_id": host_id,
                "dispatch_token": dispatch["dispatch_token"], "created": True, "project_association_confirmed": True,
                "project_id": dispatch["project_id"], "handoff_file": dispatch["handoff_file"],
                "successor_prompt_file": dispatch["prompt_file"], "creation_response_file": dispatch["response_file"], "created_at": stamp})
chain.update(state="active", parent_thread_id=OWNER, owner_thread_id=thread_id, owner_host_id=host_id,
             successor_created=True, creation_response_file=dispatch["response_file"], dispatch_ready_for=None,
             current_stage="not_started_owner_registered", last_stage_evidence=dispatch["assessment_file"],
             resume_character="Warg", resume_stage="Verify active ownership token, inspect Warg source, and establish its own baseline",
             ownership_transfer_note="Fresh local Warg thread confirmed and registered. Child owns subsequent production/Unity work; parent stops all workspace writes.",
             updated_at=stamp)
write(chain_path, chain)
print(json.dumps({"state": "active", "thread_id": thread_id, "host_id": host_id, "character": "Warg", "sequence": sequence,
                  "dispatch_token": dispatch["dispatch_token"], "project_association_confirmed": True}, ensure_ascii=False))
