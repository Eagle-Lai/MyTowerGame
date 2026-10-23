"""Read existing R3 evidence and project files; write this Docs folder only."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = REVIEW.parents[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


timestamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
expected = json.loads((REVIEW / "implementation_fingerprint.json").read_text(encoding="utf-8-sig"))
implementation = [{"path": name, "r3_sha256": value, "current_sha256": digest(ROOT / name)}
                  for name, value in expected.items()]
implementation_drift = [entry for entry in implementation if entry["r3_sha256"] != entry["current_sha256"]]

previous_scope = json.loads((REVIEW / "prefab_scope_audit.json").read_text(encoding="utf-8-sig"))
prefabs = sorted((ROOT / "Assets/Prefabs/Enemy").glob("*.prefab"), key=lambda path: path.name)
prefab_scope = [{**entry, "current_sha256": digest(ROOT / "Assets/Prefabs/Enemy" / entry["name"])}
                for entry in previous_scope["files"]]
prefab_drift = [entry["name"] for entry in prefab_scope if entry["after"] != entry["current_sha256"]]
changed_from_original = [entry["name"] for entry in prefab_scope if entry["before"] != entry["current_sha256"]]
catalog_matches = [path.name for path in prefabs] == [entry["name"] for entry in prefab_scope]

source_paths = []
for directory in (ROOT / "Assets", ROOT / "Packages"):
    for path in directory.rglob("*"):
        if path.is_file() and (path.suffix in (".cs", ".asmdef", ".asmref")
                               or path.name in ("manifest.json", "packages-lock.json")):
            source_paths.append(path)
source_manifest = [{"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "bytes": path.stat().st_size}
                   for path in sorted(source_paths)]

references = [ROOT / "Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png",
              ROOT / "Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png.meta",
              ROOT / "Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.prefab",
              ROOT / "Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.prefab.meta",
              ROOT / "Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab.meta"]
references.extend(path for path in (ROOT / "Assets/_UIAssets/Monsters/_Common/Animations/Rooster").iterdir() if path.is_file())
reference_drift = subprocess.run(["git", "diff", "--name-only", "HEAD", "--"] + [str(path) for path in references],
                                 cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()

evidence_names = ["four_directions.png", "up_down_walk.gif", "walk_turn.gif", "attack_death_reuse.gif",
                  "actual_runtime_checks.txt", "pause_speed_checks.txt", "path_refresh_checks.txt",
                  "action_pool_checks.txt", "reapply_check.txt", "dependencies.txt", "collector_coverage.txt",
                  "VALIDATION.md", "unity_final_state.txt", "progress.json"]
evidence = [{"path": name, "sha256": digest(REVIEW / name)} for name in evidence_names]
checks = (REVIEW / "actual_runtime_checks.txt").read_text(encoding="utf-8-sig").splitlines()
summary = {
    "observed_at": timestamp,
    "project": str(ROOT),
    "mode": "read_only_recheck_of_existing_R3_no_new_play_or_compile",
    "implementation_checked": len(implementation),
    "implementation_drift": implementation_drift,
    "prefab_count": len(prefabs),
    "catalog_matches_R3": catalog_matches,
    "prefab_drift_from_R3": prefab_drift,
    "prefabs_changed_from_original_local_baseline": changed_from_original,
    "reference_changes_vs_HEAD": reference_drift,
    "source_manifest_count": len(source_manifest),
    "existing_R3_recorded_pass": sum(line.startswith("PASS ") for line in checks),
    "existing_R3_recorded_fail": sum(line.startswith("FAIL ") for line in checks),
    "runtime_checks_repeated_this_recheck": False,
    "review_gate": "awaiting_explicit_user_approval",
}
write_json("implementation_comparison.json", implementation)
write_json("prefab_comparison.json", prefab_scope)
write_json("source_manifest.json", source_manifest)
write_json("reference_fingerprint.json", [{"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path)} for path in sorted(references)])
write_json("existing_evidence_fingerprint.json", evidence)
write_json("summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
