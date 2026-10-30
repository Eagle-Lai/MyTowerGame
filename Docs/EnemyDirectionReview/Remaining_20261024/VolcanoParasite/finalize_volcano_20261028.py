"""Seal the reviewed R03 candidate; retain all rejected versions and source evidence."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import ast
import hashlib
import json
import re
import subprocess
import sys

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
NAME = "VolcanoParasite"
OWNER = "01a18283-6ed7-71f0-97f7-6cc97bba20ff"
TOKEN = "turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c"
RUNS = ["runtime_r03", "runtime_updeath_r03"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def data(value):
    return value.get("structuredContent") or json.loads(value["content"][0]["text"])


chain_path = H / "conversation_chain.json"
progress_path = H / "progress.json"
chain = read(chain_path)
assert chain["state"] == "active" and chain["owner_thread_id"] == OWNER
assert chain["dispatch_token"] == TOKEN and chain["current_character"] == NAME
progress = read(progress_path)
item = next(row for row in progress["items"] if row["name"] == NAME)
assert item["status"] == "staged_pending_visual_check" and item["user_approved"] is False
assert progress["completed_count"] == 90
assert not (D / "final_validation_20261028.json").exists()

baseline_path = D / "incremental_before_20261028.json"
baseline = read(baseline_path)
before = {p: digest.upper() for p, digest in baseline["files"].items()}
assert len(before) == 5365
current = {p.relative_to(ROOT).as_posix(): sha(p)
           for folder in ["Assets", "Packages", "ProjectSettings", "Luban"]
           for p in (ROOT / folder).rglob("*") if p.is_file()}
manifest_paths = ["repair_proportions_r02/manifest.json", "repair_pool_rotation_r03/manifest.json"]
m2, m3 = [read(D / p) for p in manifest_paths]
assert m2["verification"]["data"]["result"]["pass"] is True
assert m3["verification"]["verified"] is True
assert (D / "repair_pool_rotation_r03/verify.txt").read_text(encoding="utf-8-sig").strip() == m3["verification"]["report"].strip()
assert all(line.startswith("PASS ") for line in m3["verification"]["report"].splitlines())
installed = {row["path"]: row["after"].upper() for row in m2["changes"]}
assert len(installed) == 21 and len(m3["changes"]) == 2
for row in m3["changes"]:
    assert installed[row["path"]] == row["before"].upper()
    installed[row["path"]] = row["after"].upper()
assert all(current.get(path) == digest for path, digest in installed.items()), "Final R02+R03 fingerprint drift"

battle = "Assets/Prefabs/Enemy/Enemy_VolcanoParasite.prefab"
art = "Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/Directions"
assert all(p in [battle, battle + ".meta"] or p.startswith(art + "/") for p in installed)
changes = [{"path": p, "before": before.get(p), "after": current.get(p)}
           for p in sorted(set(before) | set(current)) if before.get(p) != current.get(p)]
side_effects = []
for row in changes:
    if row["path"] == "Assets/StreamingAssets/build_info":
        reporter = "Assets/Reporter/Editor/ReporterEditor.cs"
        assert current[reporter] == before[reporter]
        assert re.fullmatch(r"Build from .+ at .+", (ROOT / row["path"]).read_text(encoding="utf-8"))
        side_effects.append(dict(row, origin="Unmodified ReporterEditor Play timestamp"))
allowed = set(installed) | {art + ".meta"} | {row["path"] for row in side_effects}
unexpected = [row for row in changes if row["path"] not in allowed]
assert not unexpected, unexpected
protected = {p: v.upper() for p, v in baseline["protected_six"].items()}
assert len(protected) == 6
protected_drift = [p for p, v in protected.items() if p != battle and current.get(p) != v]
assert not protected_drift
assert all(sha(D / "reference" / Path(p).name) == v for p, v in protected.items() if p != battle)
shared_cs_drift = [p for p in set(before) | set(current) if p.endswith(".cs") and before.get(p) != current.get(p)]
assert not shared_cs_drift
audit_source = H.parent / "Batch01_10/audit_scope.py"
tree = ast.parse(audit_source.read_text(encoding="utf-8-sig"))
definitions = ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef)], type_ignores=[])
namespace = {"re": re, "hashlib": hashlib, "HERE": H, "ROOT": ROOT, "targets": {NAME: {"battle": battle}}}
exec(compile(definitions, str(audit_source), "exec"), namespace)
semantic = namespace["semantic"](NAME)
assert semantic["pass"], semantic

preinstall = read(D / "preinstall_review_20261028.json")
assert len(preinstall["parts"]) == 12
assert all(p["enclosed_alpha_holes"] == 0 and p["opaque_magenta_pixels"] == 0 for p in preinstall["parts"].values())
assert read(D / "local_raster_revision_01.json")["filled_pixels"] == 11
staged_hashes = {}
for filename in [NAME + "_Directions.png", NAME + "_Directions.sprites.json", NAME + "_Directions.layout.json"]:
    staged_hashes[filename] = sha(D / "staged_art" / filename)
    assert staged_hashes[filename] == current[art + "/" + filename]
runtime = read(D / "runtime_summary.json")
assert runtime["passes"] == 168 and runtime["failures"] == 0 and runtime["actual_frames"] == 592
assert [r["revision"] for r in runtime["runtime"]] == RUNS
frames = {}
for run in runtime["runtime"]:
    revision = run["revision"]
    folder = D / revision
    assert (run["pass"], run["fail"], run["frames"]) == (84, 0, 296)
    assert sha(folder / "actual_frames.jsonl") == run["records_sha256"]
    rows = [json.loads(line) for line in (folder / "actual_frames.jsonl").read_text(encoding="utf-8-sig").splitlines() if line]
    checks = (folder / "actual_runtime_checks.txt").read_text(encoding="utf-8-sig").splitlines()
    assert len(rows) == 296 and sum(x.startswith("PASS ") for x in checks) == 84
    assert not any(x.startswith("FAIL ") for x in checks)
    assert all(a["frame"] < b["frame"] and a["realtime"] < b["realtime"] for a, b in zip(rows, rows[1:]))
    assert all(row["shadow"] is False for row in rows)
    frames[revision] = {row["file"]: sha(folder / row["file"]) for row in rows}
    assert len(frames[revision]) == 296 and all(frames[revision].values())
    assert len(list((folder / "frames").glob("*.png"))) == 296
    start = read(D / (revision + "_start.json"))
    assert start["project"]["projectRoot"].lower() == "e:/mytowergame" and start["project"]["unityVersion"] == "2022.3.62f3c1"
    assert start["name"] == NAME and start["revision"] == revision and data(start["response"])["data"]["result"] is True
    assert read(D / (revision + "_returned.json"))["state"] == {"playing": False, "review": False, "scene": "Assets/Scenes/Boot.unity", "dirty": False}
assert read(D / "runtime_updeath_r03_start.json")["death_up"] is True
all_gifs = {run: {p.name: sha(p) for p in sorted((D / run).glob("*.gif"))}
            for run in ["runtime_r01", "runtime_updeath_r01", "runtime_r02", "runtime_updeath_r02", *RUNS]}
assert all(len(files) == 6 for files in all_gifs.values())
samples = read(D / "gif_samples_r03_20261028/samples.json")
assert len(samples["samples"]) == 60
assert len({(r["revision"], r["file"]) for r in samples["samples"]}) == 12
assert all(all_gifs[r["revision"]][r["file"]] == r["gif_sha256"] for r in samples["samples"])

probe_path = D / "unity_final_probe_20261028_response.json"
probe = read(probe_path)
assert probe["success"] and probe["transport"] == "http://127.0.0.1:8088/mcp"
assert probe["project"]["projectRoot"].lower() == "e:/mytowergame"
state = probe["results"][0]["data"]
errors = data(probe["results"][1])
live = data(probe["results"][2])["data"]["result"]
assert errors["success"] and errors["data"] == []
assert state["advice"]["ready_for_tools"] and not state["tests"]["is_running"]
assert not state["compilation"]["is_compiling"] and not state["compilation"]["is_domain_reload_pending"] and not state["assets"]["is_updating"]
assert live["projectRoot"].replace("\\", "/").lower() == "e:/mytowergame" and live["unityVersion"] == "2022.3.62f3c1"
assert all(live[k] is False for k in ["playing", "compiling", "failed", "updating", "sceneDirty", "balance", "recording", "review", "manual"])
assert live["scene"] == "Assets/Scenes/Boot.unity" and live["sceneCount"] == 1

reviewed_images = ["offline_proof_uncropped_r03.png", "runtime_visual_strip.png"]
reviewed_images += [f"{run}/four_directions.png" for run in RUNS]
reviewed_images += [f"visual_review_r03_20261028/{run}_{suffix}.png" for run in RUNS
                    for suffix in ["sequence_0", "sequence_1", "sequence_2", "walk_cycle", "angry_detail"]]
reviewed_images += [f"gif_samples_r03_20261028/{run}_samples.png" for run in RUNS]
full_size = ["runtime_r03/frames/Attack_00118.png", "runtime_r03/frames/Hurt_00137.png", "runtime_r03/frames/Hurt_00139.png",
             "runtime_updeath_r03/frames/DeathAutoRecycle_00145.png", "runtime_r03/frames/ContinuousTurns_00228.png",
             "runtime_r03/frames/ContinuousTurns_00264.png", "runtime_r03/frames/ContinuousTurns_00274.png",
             "runtime_updeath_r03/frames/ContinuousTurns_00239.png"]
visual_note = ("R03实际审阅两轮四向图、10张动作/步态/愤怒顺序板、运行条、8张原尺寸PNG、无裁切离线解剖图，"
               "及最终12个GIF各5个编码帧样本共60帧。Up无脸无牙后视，Down上下两排牙；无眼足翼，四段爬行连接正常。"
               "攻击前压、受击白闪恢复、两向死亡淡出/缩小与复用、暂停倍速均有抽样证据；R03复用后连续左右转向背角朝上，R02倒置已消除。"
               "R01体量偏小及R02旋转残留均否决，旧证据保留。GIF为编码帧抽样，非实时播放或逐GIF全帧审阅；用户美术批准待进行。")
visual = {"reviewed_at": now(), "owner_thread_id": OWNER, "dispatch_token": TOKEN, "revision": "R03", "runs": RUNS,
          "reviewed_images": {p: sha(D / p) for p in reviewed_images}, "selected_original_pngs": {p: sha(D / p) for p in full_size},
          "gif_sampling": {"method": samples["method"], "gif_count": 12, "sample_count": 60,
                           "manifest": "gif_samples_r03_20261028/samples.json", "sha256": sha(D / "gif_samples_r03_20261028/samples.json")},
          "observations": visual_note, "limitations": ["Encoded GIF frame sampling, not real-time playback or exhaustive every-frame review.",
          "Sequence-board crop can truncate top horns; uncropped offline proof and original PNGs distinguish this from production cropping.",
          "Source HP bar can overlap the upper horn during horizontal poses; retained original UI positioning."],
          "rejected_revisions": {"R01": "Axial Up/Down too small relative to retained horizontal source.",
                                 "R02": "After death reuse, inherited horizontal Body rotation inverted Left/Right."},
          "final_r03_fix": "Only dedicated Ready/Walk clips add constant-zero Body localEulerAnglesRaw x/y/z; original curves/events/timing retained.",
          "technical_visual_pass": True, "user_approved": False}
assert all(visual["reviewed_images"].values()) and all(visual["selected_original_pngs"].values())
visual_path = D / "visual_review_r03_20261028/review.json"
assert not visual_path.exists()
write(visual_path, visual)
note_path = D / "record_note_utf8.txt"
note_path.write_text(visual_note + "\n", encoding="utf-8")
runtime.update(status="completed_pending_user_art_review", visual_reviewed=True, visual_review_file="visual_review_r03_20261028/review.json",
               visual_note=visual_note, user_approved=False, final_revision="R03")
write(D / "runtime_summary.json", runtime)

scope = {"observed_at": now(), "baseline": baseline_path.name, "baseline_sha256": sha(baseline_path), "baseline_files": len(before),
         "current_files": len(current), "comparison": "Full path union across Assets/Packages/ProjectSettings/Luban, never Git HEAD.",
         "changes": changes, "unexpected_incremental": unexpected, "automatic_editor_side_effects": side_effects,
         "protected_six": protected, "protected_drift": protected_drift, "shared_CSharp_drift": shared_cs_drift,
         "installed_manifest_paths": installed, "manifest_composition": manifest_paths, "installed_manifest_drift": [],
         "staged_to_installed_hashes": staged_hashes, "prefab_semantics": semantic,
         "semantic_method": "Reused only definition AST nodes from Batch01_10/audit_scope.py; character baseline is VolcanoParasite/reference.",
         "stage_part_count": 12, "stage_alpha_holes": 0, "stage_alpha_repaired_pixels": 11,
         "legacy_global_note": "Old global audit's 291 unexpected paths and six historical semantic failures remain separate; no global PASS claim."}
scope_path = D / "scope_incremental_final_20261028.json"
write(scope_path, scope)
archive_manifest_path = H.parent / "AllGIF/manifest.json"
archive_before = read(archive_manifest_path)["count"]
record = subprocess.run([sys.executable, str(H / "record_review.py"), NAME, visual_note], capture_output=True, check=True, text=True, encoding="utf-8")
progress = read(progress_path)
item = next(row for row in progress["items"] if row["name"] == NAME)
assert progress["completed_count"] == 91 and item["status"] == "completed_pending_user_art_review" and item["user_approved"] is False
assert item["actual_frames"] == 592 and item["runtime"] == runtime["runtime"]
archive_manifest = read(archive_manifest_path)
archives = {r["source"]: r for r in archive_manifest["files"]}
pairs = []
for run, files in all_gifs.items():
    for filename, digest in files.items():
        source = f"Remaining_20261024/{NAME}/{run}/{filename}"
        row = archives[source]
        assert row["sha256"] == digest and sha(H.parent / "AllGIF" / row["file"]) == digest
        assert row["status"] == ("当前审核版本" if run in RUNS else "历史或准备材料")
        pairs.append({"source": source, "archive": row["file"], "sha256": digest, "status": row["status"]})
assert len(pairs) == 36
archive_report = {"verified_at": now(), "source_gif_count": 36, "matching_archive_count": 36, "final_review_gifs": 12,
                  "historical_gifs": 24, "global_archive_count_before": archive_before, "global_archive_count": archive_manifest["count"],
                  "all_source_and_archive_sha256_match": True, "files": pairs, "manifest_sha256": sha(archive_manifest_path)}
archive_path = D / "gif_archive_verification_20261028.json"
write(archive_path, archive_report)
remaining = [row for row in progress["items"] if row["status"] not in ["completed_pending_user_art_review", "user_approved"]]
recoverable = [row for row in remaining if row["status"] not in ["not_started", "blocked"]]
candidates = recoverable or [row for row in remaining if row["status"] != "blocked"]
next_item = min(candidates, key=lambda row: row["index"]) if candidates else None
assert next_item and next_item["name"] == "Warg"
item.update(stage="recorded_pending_user_art_review", final_revision="R03", final_validation_file=NAME + "/final_validation_20261028.json",
            version_binding_file=NAME + "/version_binding_final_20261028.json", scope_file=NAME + "/scope_incremental_final_20261028.json",
            visual_review_file=NAME + "/visual_review_r03_20261028/review.json", gif_archive_file=NAME + "/gif_archive_verification_20261028.json")
progress.update(current=next_item["name"], updated_at=now())
evidence = {p.relative_to(D).as_posix(): sha(p) for p in sorted(D.rglob("*"))
            if p.is_file() and "frames" not in p.relative_to(D).parts
            and p.name not in ["version_binding_final_20261028.json", "final_validation_20261028.json"]}
binding = {"observed_at": now(), "final_revision": "R03", "manifest_composition": {p: sha(D / p) for p in manifest_paths},
           "installed_files": installed, "production_scope_files": {row["path"]: row["after"] for row in changes},
           "files": evidence, "actual_png_frames": frames, "frame_total": 592,
           "external_evidence": {"ProjectSettings/ProjectVersion.txt": sha(ROOT / "ProjectSettings/ProjectVersion.txt"),
                                 "unity_final_probe": sha(probe_path), "gif_archive_verification": sha(archive_path)},
           "note": "R02 full 21-path fingerprint overridden only by R03 two dedicated animation hashes; binds 592 final PNGs, 12 final/24 historical GIFs, checks, visual sampling and current Unity identity."}
binding_path = D / "version_binding_final_20261028.json"
write(binding_path, binding)
final = {"observed_at": now(), "character": NAME, "owner_thread_id": OWNER, "dispatch_token": TOKEN,
         "status": "completed_pending_user_art_review", "user_approved": False, "final_revision": "R03",
         "passes": 168, "failures": 0, "actual_png_frames": 592, "runtime": runtime["runtime"], "installer_verify_pass": True,
         "manifest_composition": binding["manifest_composition"], "incremental_scope_file": scope_path.name, "incremental_scope_sha256": sha(scope_path),
         "incremental_changes": len(changes), "incremental_unexpected": 0, "prefab_semantic_pass": semantic["pass"],
         "version_binding_file": binding_path.name, "version_binding_sha256": sha(binding_path),
         "visual_review_file": "visual_review_r03_20261028/review.json", "visual_review_sha256": sha(visual_path),
         "gif_archive_file": archive_path.name, "gif_archive_sha256": sha(archive_path), "archived_character_gifs": 36,
         "final_review_gifs": 12, "global_archive_count": archive_manifest["count"],
         "unity": {"transport": probe["transport"], "project": probe["project"], "instance_id": state["unity"]["instance_id"],
                   "live_probe": live, "ready_for_tools": True, "console_errors": 0,
                   "external_changes_dirty": state["assets"]["external_changes_dirty"], "evidence": probe_path.name},
         "progress": {"completed_count": 91, "authorized_count": progress["authorized_count"], "next_candidate": next_item["name"]},
         "record_review_output": record.stdout.strip(), "legacy_global_scope_warning": scope["legacy_global_note"]}
write(D / "final_validation_20261028.json", final)
write(progress_path, progress)
chain = read(chain_path)
assert chain["owner_thread_id"] == OWNER and chain["dispatch_token"] == TOKEN and chain["state"] == "active"
chain.update(current_stage="recorded_pending_user_art_review", last_stage_evidence="Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/final_validation_20261028.json", updated_at=now())
write(chain_path, chain)
print(json.dumps({"character": NAME, "status": final["status"], "completed_count": 91, "scope_changes": len(changes),
                  "current_files": len(current), "scope_unexpected": 0, "semantic_pass": True, "passes": 168, "failures": 0,
                  "frames": 592, "archived_gifs": 36, "global_archive_count": archive_manifest["count"], "next": next_item["name"]}, ensure_ascii=False))
