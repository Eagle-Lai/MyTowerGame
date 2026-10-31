from search import *
DOC=ROOT/'Docs/BalanceEvidence/L03-CurrentModel-20261025'
c=client();results={}
results['identity']=c.identity
results['state']=c.resource('mcpforunity://editor/state')
results['console']=c.call('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
results['runtimeHashLog']=c.call('read_console',{'action':'get','types':['log'],'filter_text':'Runtime configuration SHA256 verified','count':'5','format':'json'})
code='return new { state=FTProject.GameFlowManager.Instance.State.ToString(), hp=FTProject.PlayerDataManager.Instance.Hp, gold=FTProject.PlayerDataManager.Instance.Gold, towers=FTProject.TowerManager.Instance.Count, metrics=UnityEngine.JsonUtility.ToJson(FTProject.GameFlowManager.Instance.RunMetrics), compilationFailed=UnityEditor.EditorUtility.scriptCompilationFailed };'
results['liveResult']=c.call('execute_code',{'action':'execute','code':code})
results['screenshot']=c.call('manage_camera',{'action':'screenshot','screenshot_file_name':'L03-最终结算.png','output_folder':str(DOC).replace(chr(92),'/'),'include_image':False})
dump(DOC/'editor-final-verification.json',results)
print(json.dumps(results,ensure_ascii=False))
