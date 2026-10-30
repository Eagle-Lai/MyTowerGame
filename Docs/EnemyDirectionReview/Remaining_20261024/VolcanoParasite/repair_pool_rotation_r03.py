"""Reset only VolcanoParasite's dedicated horizontal idle/walk body rotation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = HERE.parent
REV = HERE / "repair_pool_rotation_r03"
sys.path.insert(0, str(TASK))
from mcp_call import Client


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def unwrap(value):
    value = value.get("structuredContent") or json.loads(value["content"][0]["text"])
    if not value.get("success"):
        raise RuntimeError(str(value))
    return value["data"]["result"]


if REV.exists():
    raise RuntimeError("R03 evidence already exists; inspect before retrying")
progress = json.loads((TASK / "progress.json").read_text(encoding="utf-8"))
item = next(value for value in progress["items"] if value["name"] == "VolcanoParasite")
if progress["current"] != "VolcanoParasite" or item["status"] != "staged_pending_visual_check":
    raise RuntimeError("Unexpected live progress; refusing repair")

manifest_path = HERE / "repair_proportions_r02" / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
for change in manifest["changes"]:
    path = ROOT / change["path"]
    if not path.is_file() or sha(path) != change["after"]:
        raise RuntimeError("Installed R02 drift: " + change["path"])

client = Client()
project = client.identity()
probe = unwrap(client.tool("execute_code", {"action": "execute", "code":
    "return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,failed=UnityEditor.EditorUtility.scriptCompilationFailed,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};"}))
if any(probe.values()):
    raise RuntimeError("Editor is busy or scene is dirty: " + str(probe))

clips = [ROOT / "Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/Directions/Animations/" / (name + "_Directions.anim") for name in ("Ready", "Walk")]
before = {path.relative_to(ROOT).as_posix(): sha(path) for path in clips}
REV.mkdir()
for path in clips:
    backup = REV / "before" / path.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
shutil.copy2(HERE / "runtime_summary.json", REV / "runtime_summary_r02.json")
shutil.copy2(HERE / "runtime_visual_strip.png", REV / "runtime_visual_strip_r02.png")
(REV / "baseline.json").write_text(json.dumps({
    "name": "VolcanoParasite", "previous_revision": "repair_proportions_r02",
    "project": project, "editor_state": probe, "clip_sha256_before": before,
    "repair": "Add zero-valued local Euler curves to Body in dedicated Ready/Walk copies so returning from the original death rotation cannot leave the side-facing worm inverted.",
    "captured_at": datetime.now(timezone.utc).isoformat(),
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

code = r'''if(UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode || UnityEditor.EditorApplication.isCompiling || UnityEditor.EditorApplication.isUpdating) throw new System.InvalidOperationException("Editor busy");
string folder="Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/Directions/Animations/";
var changed=new System.Collections.Generic.List<string>();
foreach(string action in new[]{"Ready","Walk"}) {
 var source=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Parasite/"+action+".anim");
 var clip=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.AnimationClip>(folder+action+"_Directions.anim");
 if(!source || !clip) throw new System.InvalidOperationException("Missing source or dedicated clip: "+action);
 foreach(var binding in UnityEditor.AnimationUtility.GetCurveBindings(source))
  if(binding.path=="Body" && binding.propertyName.StartsWith("localEulerAnglesRaw.")) throw new System.InvalidOperationException("Source Body Euler binding already exists: "+action);
 foreach(string axis in new[]{"x","y","z"}) {
  var binding=UnityEditor.EditorCurveBinding.FloatCurve("Body",typeof(UnityEngine.Transform),"localEulerAnglesRaw."+axis);
  if(UnityEditor.AnimationUtility.GetEditorCurve(clip,binding)!=null) throw new System.InvalidOperationException("Dedicated Body Euler binding already exists: "+action+" "+axis);
  UnityEditor.AnimationUtility.SetEditorCurve(clip,binding,UnityEngine.AnimationCurve.Constant(0,clip.length,0));
 }
 UnityEditor.EditorUtility.SetDirty(clip); changed.Add(folder+action+"_Directions.anim");
}
UnityEditor.AssetDatabase.SaveAssets();
FTProject.EditorTools.EnemyDirectionSpec spec;
if(!FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("VolcanoParasite",out spec)) throw new System.InvalidOperationException("Missing direction spec");
string report; bool verified=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out report);
return new {changed=changed,verified=verified,report=report};'''
result = unwrap(client.tool("execute_code", {"action": "execute", "code": code}))
if not result["verified"]:
    raise RuntimeError("Post-repair rig verification failed: " + result["report"])
after = {path.relative_to(ROOT).as_posix(): sha(path) for path in clips}
changes = [{"path": key, "before": before[key], "after": after[key]} for key in before]
if any(change["before"] == change["after"] for change in changes):
    raise RuntimeError("Expected both dedicated clips to change")
(REV / "manifest.json").write_text(json.dumps({
    "name": "VolcanoParasite", "revision": "repair_pool_rotation_r03",
    "previous_manifest": "../repair_proportions_r02/manifest.json",
    "changes": changes, "verification": result,
    "protocol_history": client.history,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(REV / "verify.txt").write_text(result["report"], encoding="utf-8")
print(json.dumps({"revision": "repair_pool_rotation_r03", "verified": True, "changes": changes}, ensure_ascii=False))
