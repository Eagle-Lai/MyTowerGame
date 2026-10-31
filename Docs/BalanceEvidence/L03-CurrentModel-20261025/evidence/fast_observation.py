from search import *
code='''UnityEditor.SessionState.SetBool("FT.L03.DisableReentryObserver",true);
UnityEditor.EditorApplication.CallbackFunction observer=null;
observer=()=>{if(!UnityEditor.SessionState.GetBool("FT.L03.DisableReentryObserver",false)){UnityEditor.EditorApplication.update-=observer;return;} FTProject.BaseTower.EvidenceTrackReentry=false;};
UnityEditor.EditorApplication.update+=observer;
FTProject.BaseTower.EvidenceTrackReentry=false;
return "Repeated-range observer disabled; targeting, damage, economy, waves and outcome events unchanged";'''
print(execute(code))
