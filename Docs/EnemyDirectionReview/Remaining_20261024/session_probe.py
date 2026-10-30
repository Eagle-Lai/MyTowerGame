from pathlib import Path
import json
from datetime import datetime
from mcp_call import Client
c=Client()
report={"identity":c.identity(),"state":c.resource("mcpforunity://editor/state")}
report["probe"]=c.tool("execute_code",{"action":"execute","code":"return new {failed=UnityEditor.EditorUtility.scriptCompilationFailed,playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,updating=UnityEditor.EditorApplication.isUpdating,dirty=UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty};"})
report["errors"]=c.tool("read_console",{"action":"get","types":["error"],"count":"50","format":"json"})
report["history"]=c.history
path=Path(__file__).parent/("session_probe_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".json")
path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k!="history"},ensure_ascii=False))
