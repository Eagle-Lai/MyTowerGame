"""Seal Turkey's installed, runtime, visual, and incremental-scope evidence."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = "Turkey"
OWNER = "01a18233-1a0c-7653-9ac2-6ecd99754a92"
TOKEN = "troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309"
RUNS = ["runtime_r01", "runtime_updeath_r01"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def inventory():
    return {
        path.relative_to(ROOT).as_posix(): sha(path)
        for folder in ["Assets", "Packages", "ProjectSettings", "Luban"]
        for path in (ROOT / folder).rglob("*")
        if path.is_file()
    }


def result_data(value):
    return value.get("structuredContent") or json.loads(value["content"][0]["text"])


chain_path = H / "conversation_chain.json"
progress_path = H / "progress.json"
chain = read(chain_path)
assert chain["state"] == "active"
assert chain["owner_thread_id"] == OWNER and chain["dispatch_token"] == TOKEN
assert chain["current_character"] == NAME
progress = read(progress_path)
item = next(row for row in progress["items"] if row["name"] == NAME)
assert item["status"] == "reference_prepared" and item.get("user_approved") is False
assert item.get("stage") == "installed_pending_runtime"

baseline_path = D / "incremental_before_20261028.json"
baseline = read(baseline_path)
before = {path: digest.upper() for path, digest in baseline["files"].items()}
assert len(before) == 5345
current = inventory()
manifest = read(D / "installed_manifest.json")
assert manifest["name"] == NAME
assert manifest["verification"]["data"]["result"]["pass"] is True
verify_text = (D / "installed_verify.txt").read_text(encoding="utf-8-sig")
assert verify_text == manifest["verification"]["data"]["result"]["report"]
assert verify_text.splitlines() and all(line.startswith("PASS ") for line in verify_text.splitlines())
installed = {entry["path"]: entry["after"].upper() for entry in manifest["changes"]}
assert len(installed) == 20
assert all(current.get(path) == digest for path, digest in installed.items())

battle = "Assets/Prefabs/Enemy/Enemy_Turkey.prefab"
art = "Assets/_UIAssets/Monsters/Birds/Turkey/Directions"
directory_meta = art + ".meta"
changes = [
    {"path": path, "before": before.get(path), "after": current.get(path)}
    for path in sorted(set(before) | set(current))
    if before.get(path) != current.get(path)
]
unity_metadata = {}
if before.get(directory_meta) != current.get(directory_meta):
    assert current.get(directory_meta) is not None
    unity_metadata[directory_meta] = current[directory_meta]

side_effects = []
for change in changes:
    path = change["path"]
    if path in installed or path in unity_metadata:
        continue
    if path == "Assets/StreamingAssets/build_info":
        reporter = "Assets/Reporter/Editor/ReporterEditor.cs"
        build_info = (ROOT / path).read_text(encoding="utf-8")
        assert current.get(reporter) == before.get(reporter)
        assert re.fullmatch(r"Build from .+ at .+", build_info)
        side_effects.append(dict(change, origin="Unmodified ReporterEditor Play timestamp"))

allowed_paths = set(installed) | set(unity_metadata) | {row["path"] for row in side_effects}
unexpected = [row for row in changes if row["path"] not in allowed_paths]
assert not unexpected, unexpected
assert {row["path"] for row in changes} == allowed_paths

protected = {path: digest.upper() for path, digest in baseline["protected_six"].items()}
protected_drift = [
    path for path, digest in protected.items()
    if path != battle and current.get(path) != digest
]
assert not protected_drift, protected_drift
for path, digest in protected.items():
    if path == battle:
        continue
    reference = D / "reference" / Path(path).name
    assert sha(reference) == digest
shared_cs_drift = [
    path for path in set(before) | set(current)
    if path.endswith(".cs") and before.get(path) != current.get(path)
]
assert not shared_cs_drift, shared_cs_drift

staged_review = read(D / "staged_review_20261028.json")
assert staged_review["baseline_sha256"] == sha(baseline_path)
assert staged_review["baseline_files"] == len(before)
assert staged_review["alpha_pass"] is True
assert len(staged_review["alpha"]) == 14
assert all(row["internal_transparent_holes"] == 0 for row in staged_review["alpha"].values())
assert staged_review["layout_anatomy"]["legs"] == 2
assert staged_review["layout_anatomy"]["wings"] == 2
assert staged_review["layout_anatomy"]["tails"] == 1
alpha_repair = read(D / "alpha_repair_20261028.json")
assert alpha_repair["filled_pixels_total"] == 1004
assert alpha_repair["atlas_after_sha256"] == sha(D / "staged_art/Turkey_Directions.png")
for staged_name in ["Turkey_Directions.png", "Turkey_Directions.sprites.json", "Turkey_Directions.layout.json"]:
    source = D / "staged_art" / staged_name
    production = ROOT / art / staged_name
    assert sha(source) == staged_review["staged_art"][staged_name]
    assert sha(source) == sha(production)

runtime = read(D / "runtime_summary.json")
assert runtime["passes"] == 168 and runtime["failures"] == 0
assert runtime["actual_frames"] == 686
assert [row["revision"] for row in runtime["runtime"]] == RUNS
actual_png_frames = {}
all_gifs = {}
for run in runtime["runtime"]:
    revision = run["revision"]
    folder = D / revision
    assert run["pass"] == 84 and run["fail"] == 0 and run["frames"] == 343
    records_path = folder / "actual_frames.jsonl"
    assert sha(records_path) == run["records_sha256"]
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8-sig").splitlines() if line]
    checks = (folder / "actual_runtime_checks.txt").read_text(encoding="utf-8-sig").splitlines()
    assert len(records) == 343
    assert sum(line.startswith("PASS ") for line in checks) == 84
    assert not any(line.startswith("FAIL ") for line in checks)
    assert all(left["frame"] < right["frame"] and left["realtime"] < right["realtime"] for left, right in zip(records, records[1:]))
    assert all(row["shadow"] is False for row in records)
    frames = {}
    for row in records:
        filename = row["file"]
        frame_path = folder / filename
        assert frame_path.is_file() and frame_path.resolve().is_relative_to(folder.resolve())
        assert filename not in frames
        frames[filename] = sha(frame_path)
    assert len(frames) == 343
    actual_png_frames[revision] = frames
    assert len(list(folder.glob("*.gif"))) == 6
    all_gifs[revision] = {path.name: sha(path) for path in sorted(folder.glob("*.gif"))}
    start = read(D / f"{revision}_start.json")
    returned = read(D / f"{revision}_returned.json")
    assert start["name"] == NAME and start["revision"] == revision
    assert start["project"]["projectRoot"].replace("\\", "/").lower() == "e:/mytowergame"
    assert start["project"]["unityVersion"] == "2022.3.62f3c1"
    assert start["response"]["structuredContent"]["data"]["result"] is True
    assert returned["state"] == {"playing": False, "review": False, "scene": "Assets/Scenes/Boot.unity", "dirty": False}
assert sum(len(files) for files in actual_png_frames.values()) == 686
assert read(D / "runtime_updeath_r01_start.json")["death_up"] is True

sample_path = D / "visual_review_final_20261028/gif_review_samples.json"
samples = read(sample_path)
assert samples["gif_count"] == 12 and samples["sample_count"] == 60
assert len({(row["revision"], row["gif"]) for row in samples["samples"]}) == 12
for row in samples["samples"]:
    assert all_gifs[row["revision"]][row["gif"]] == row["sha256"]
board = D / "visual_review_final_20261028" / samples["board"]
assert board.is_file()

probe_files = sorted(D.glob("unity_final_probe_20261028_response*.json"), key=lambda path: path.stat().st_mtime)
probe_path = next(path for path in reversed(probe_files) if read(path).get("success") is True)
probe = read(probe_path)
assert probe["project"]["projectRoot"].replace("\\", "/").lower() == "e:/mytowergame"
assert probe["project"]["unityVersion"] == "2022.3.62f3c1"
editor_state = probe["results"][0]["data"]
errors = result_data(probe["results"][1])
live = result_data(probe["results"][2])["data"]["result"]
assert errors["data"] == []
assert editor_state["advice"]["ready_for_tools"] is True
assert editor_state["compilation"]["is_compiling"] is False
assert editor_state["compilation"]["is_domain_reload_pending"] is False
assert editor_state["assets"]["is_updating"] is False
assert editor_state["tests"]["is_running"] is False
assert live["projectRoot"].replace("\\", "/").lower() == "e:/mytowergame"
assert live["unityVersion"] == "2022.3.62f3c1"
assert live["playing"] is False and live["compiling"] is False and live["failed"] is False
assert live["updating"] is False and live["scene"] == "Assets/Scenes/Boot.unity"
assert live["sceneDirty"] is False and live["sceneCount"] == 1 and live["review"] is False

visual_note = (
    "实际审阅离线证明图、两轮四方向图、运行时条、所选原尺寸攻击/受击/死亡帧，并对12个GIF各抽看5个时间点。"
    "Up为无脸后视；Down保留正面表情，攻击清晰可读；受击闪白和死亡淡出可见；成对翅膀/腿与单尾在转向中保持连接。"
    "暂停/倍速、攻击死亡复用条均作抽样审阅。GIF抽样不是逐GIF全帧审阅，用户美术批准仍待进行。"
)
visual_report = {
    "reviewed_at": samples["sampled_at"],
    "owner_thread_id": OWNER,
    "dispatch_token": TOKEN,
    "runs": RUNS,
    "offline_proof": {"file": "offline_rig_proof.png", "sha256": sha(D / "offline_rig_proof.png")},
    "runtime_four_direction_images": {run: sha(D / run / "four_directions.png") for run in RUNS},
    "runtime_visual_strip": {"file": "runtime_visual_strip.png", "sha256": sha(D / "runtime_visual_strip.png")},
    "full_size_action_frames": "Selected original-size attack, hurt, and death PNG frames were inspected.",
    "gif_sampling": {
        "method": samples["method"],
        "gif_count": samples["gif_count"],
        "sample_count": samples["sample_count"],
        "sample_manifest": "gif_review_samples.json",
        "sample_board": samples["board"],
        "sample_board_sha256": sha(board),
    },
    "observations": [
        "Up is a faceless rear view; Down keeps its front expressions and reads clearly during attack.",
        "Hurt flash and death fade are visible in the sampled runtime evidence.",
        "Paired wings and legs and the single tail remain connected through directional rotation.",
        "Walk, turn, pause/speed, attack/death/reuse samples show connected parts and clean restoration.",
    ],
    "limitations": ["Five sampled positions from each GIF; no exhaustive playback or every-frame GIF review."],
    "user_approved": False,
    "visual_note": visual_note,
}
visual_path = D / "visual_review_final_20261028/review.json"
visual_path.parent.mkdir(parents=True, exist_ok=True)
assert not visual_path.exists()
write(visual_path, visual_report)
runtime["status"] = "completed_pending_user_art_review"
runtime["visual_reviewed"] = True
runtime["visual_review_file"] = "visual_review_final_20261028/review.json"
runtime["visual_note"] = visual_note
runtime["visual_review_limitations"] = visual_report["limitations"]
write(D / "runtime_summary.json", runtime)

note_path = D / "final_visual_note_20261028.txt"
note_path.write_text(visual_note + "\n", encoding="utf-8")
record = subprocess.run(
    [sys.executable, str(H / "record_review.py"), NAME, note_path.read_text(encoding="utf-8").strip()],
    check=True, capture_output=True, text=True, encoding="utf-8",
)
progress = read(progress_path)
item = next(row for row in progress["items"] if row["name"] == NAME)
assert item["status"] == "completed_pending_user_art_review"
assert item["user_approved"] is False and item["actual_frames"] == 686
assert item["runtime"] == runtime["runtime"]
assert progress["completed_count"] == 90

gif_manifest = read(H.parent / "AllGIF/manifest.json")
archive_files = {row["source"]: row for row in gif_manifest["files"]}
archive_pairs = []
for revision, files in all_gifs.items():
    for filename, digest in files.items():
        source = f"Remaining_20261024/{NAME}/{revision}/{filename}"
        row = archive_files[source]
        assert row["sha256"] == digest
        archived = H.parent / "AllGIF" / row["file"]
        assert sha(archived) == digest
        archive_pairs.append({"source": source, "archive": row["file"], "sha256": digest, "bytes": row["bytes"]})
assert len(archive_pairs) == 12
archive_report = {
    "verified_at": now(),
    "source_gif_count": 12,
    "matching_archive_count": len(archive_pairs),
    "global_archive_count": gif_manifest["count"],
    "all_source_and_archive_sha256_match": True,
    "files": archive_pairs,
    "manifest_sha256": sha(H.parent / "AllGIF/manifest.json"),
}
archive_path = D / "gif_archive_verification_20261028.json"
assert not archive_path.exists()
write(archive_path, archive_report)

selected_next = None
remaining = [row for row in progress["items"] if row["status"] not in ("completed_pending_user_art_review", "user_approved")]
recoverable = [row for row in remaining if row["status"] not in ("not_started", "blocked")]
candidates = recoverable or [row for row in remaining if row["status"] != "blocked"]
if candidates:
    selected_next = min(candidates, key=lambda row: row["index"])
progress["current"] = selected_next["name"] if selected_next else None
item.update(
    stage="recorded_pending_user_art_review",
    final_validation_file="Turkey/final_validation_20261028.json",
    version_binding_file="Turkey/version_binding_final_20261028.json",
    scope_file="Turkey/scope_incremental_final_20261028.json",
    visual_review_file="Turkey/visual_review_final_20261028/review.json",
    gif_archive_file="Turkey/gif_archive_verification_20261028.json",
)
progress["updated_at"] = now()

scope_report = {
    "observed_at": now(),
    "baseline": "incremental_before_20261028.json",
    "baseline_sha256": sha(baseline_path),
    "baseline_files": len(before),
    "current_files": len(current),
    "comparison": "Union of pre-install baseline and current Assets/Packages/ProjectSettings/Luban paths.",
    "changes": changes,
    "unexpected_incremental": unexpected,
    "automatic_editor_side_effects": side_effects,
    "protected_six": protected,
    "protected_drift": protected_drift,
    "shared_CSharp_drift": shared_cs_drift,
    "installed_manifest_paths": installed,
    "installed_manifest_drift": [],
    "unity_created_directory_metadata": unity_metadata,
    "staged_to_installed_hashes": {
        name: sha(D / "staged_art" / name)
        for name in ["Turkey_Directions.png", "Turkey_Directions.sprites.json", "Turkey_Directions.layout.json"]
    },
    "stage_alpha_holes": 0,
    "stage_alpha_repaired_pixels": alpha_repair["filled_pixels_total"],
    "installer_verification_pass": manifest["verification"]["data"]["result"]["pass"],
    "legacy_global_audit": "../scope_Turkey_20261028_legacy_global_baseline.json",
    "legacy_global_note": "Older task-wide baseline reports 291 pre-existing unexpected paths and six historical semantic failures; this is not Turkey's incremental audit.",
    "note": "Target battle prefab and Turkey Directions assets/root .meta, plus the validated unmodified ReporterEditor timestamp side effect if present. No global PASS claim.",
}
scope_path = D / "scope_incremental_final_20261028.json"
assert not scope_path.exists()
write(scope_path, scope_report)

evidence_files = {}
for path in sorted(D.rglob("*")):
    if not path.is_file():
        continue
    relative = path.relative_to(D).as_posix()
    if relative.startswith("runtime_r01/frames/") or relative.startswith("runtime_updeath_r01/frames/"):
        continue
    if relative in {
        "version_binding_final_20261028.json",
        "scope_incremental_final_20261028.json",
        "final_validation_20261028.json",
    }:
        continue
    evidence_files[relative] = sha(path)
installed_files = {path: current[path] for path in sorted(installed)}
production_scope_files = {row["path"]: row["after"] for row in changes}
version_binding = {
    "observed_at": now(),
    "final_install_manifest": "installed_manifest.json",
    "files": evidence_files,
    "installed_files": installed_files,
    "production_scope_files": production_scope_files,
    "external_evidence": {
        "ProjectSettings/ProjectVersion.txt": sha(ROOT / "ProjectSettings/ProjectVersion.txt"),
        "Assets/Reporter/Editor/ReporterEditor.cs": current["Assets/Reporter/Editor/ReporterEditor.cs"],
        "unity_final_probe_response": sha(probe_path),
        "unity_final_probe_transport": probe["transport"],
    },
    "actual_png_frames": actual_png_frames,
    "frame_total": 686,
    "gif_archive_manifest": "gif_archive_verification_20261028.json",
    "note": "Binds Turkey staging/install, both actual Unity runs, all 686 captured PNGs, current Unity identity/state, visual sample evidence, and source/archive GIF hashes.",
}
binding_path = D / "version_binding_final_20261028.json"
assert not binding_path.exists()
write(binding_path, version_binding)

final_report = {
    "observed_at": now(),
    "owner_thread_id": OWNER,
    "dispatch_token": TOKEN,
    "character": NAME,
    "status": "completed_pending_user_art_review",
    "user_approved": False,
    "installed_manifest": "installed_manifest.json",
    "installed_manifest_sha256": sha(D / "installed_manifest.json"),
    "installer_verify_pass": True,
    "incremental_scope_file": "scope_incremental_final_20261028.json",
    "incremental_scope_sha256": sha(scope_path),
    "incremental_changes": len(changes),
    "incremental_unexpected": 0,
    "version_binding_file": "version_binding_final_20261028.json",
    "version_binding_sha256": sha(binding_path),
    "runtime": runtime["runtime"],
    "passes": 168,
    "failures": 0,
    "actual_png_frames": 686,
    "visual_review_file": "visual_review_final_20261028/review.json",
    "visual_review_file_sha256": sha(visual_path),
    "visual_reviewed": True,
    "gif_archive_file": "gif_archive_verification_20261028.json",
    "gif_archive_file_sha256": sha(archive_path),
    "archived_turkey_gifs": 12,
    "unity": {
        "transport": probe["transport"],
        "project": probe["project"],
        "instance_id": editor_state["unity"]["instance_id"],
        "console_errors": len(errors["data"]),
        "live_probe": live,
        "ready_for_tools": editor_state["advice"]["ready_for_tools"],
        "external_changes_dirty": editor_state["assets"]["external_changes_dirty"],
        "editor_state_evidence": probe_path.name,
    },
    "progress": {"completed_count": progress["completed_count"], "next_candidate": selected_next["name"] if selected_next else None},
    "record_review_output": record.stdout.strip(),
    "legacy_global_scope_warning": "Older task-wide audit reports 291 pre-existing unexpected paths and six historical semantic failures; Turkey's incremental audit is clean.",
}
final_path = D / "final_validation_20261028.json"
assert not final_path.exists()
write(final_path, final_report)

item["final_validation_file"] = "Turkey/final_validation_20261028.json"
write(progress_path, progress)
chain = read(chain_path)
assert chain["owner_thread_id"] == OWNER and chain["dispatch_token"] == TOKEN
chain.update(
    current_stage="recorded_pending_user_art_review",
    last_stage_evidence="Docs/EnemyDirectionReview/Remaining_20261024/Turkey/final_validation_20261028.json",
    updated_at=now(),
)
write(chain_path, chain)
print(json.dumps({
    "character": NAME,
    "status": final_report["status"],
    "user_approved": False,
    "completed_count": progress["completed_count"],
    "next_candidate": final_report["progress"]["next_candidate"],
    "scope_changes": len(changes),
    "scope_unexpected": len(unexpected),
    "passes": 168,
    "failures": 0,
    "frames": 686,
    "archived_gifs": 12,
    "final_validation": str(final_path),
}, ensure_ascii=False))
