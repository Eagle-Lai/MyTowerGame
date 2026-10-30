from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,re,sys
HERE=Path(__file__).resolve().parent
RUN=HERE.parent
ROOT=RUN.parents[2]
sys.path.insert(0,str(RUN))
from mcp_call import Client
NAME='WolfMounfed'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def now():return datetime.now(timezone(timedelta(hours=8))).isoformat()
def owner():
    c=read(RUN/'conversation_chain.json')
    assert c['state']=='active' and c['current_character']==NAME and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
    assert c['dispatch_token']=='wolfhound-to-wolfmounfed-20261029_222452-68c070b7-1479-493d-aae5-005029aba3d5'
    return c
def save(p,obj):
    assert not Path(p).exists(),p
    Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unwrap(v):
    v=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert v['success'],v
    result=v.get('data',{}).get('result',v.get('data'))
    return json.loads(result) if isinstance(result,str) else result
def snapshot():return {p.relative_to(ROOT).as_posix():sha(p) for f in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/f).rglob('*') if p.is_file()}
def probe(c):
    return unwrap(c.tool('execute_code',{'action':'execute','code':'return Newtonsoft.Json.JsonConvert.SerializeObject(new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,scenes=System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount).Select(i=>new {path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}).ToArray(),balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation});'}))
def idle(p):
    assert not any(p[k] for k in ['playing','compiling','failed','updating','balance','recording','review','manual']),p
    assert p['scenes']==[{'path':'Assets/Scenes/Boot.unity','dirty':False}],p
def target():return next(t for t in read(RUN/'local_baseline.json')['targets'] if t['name']==NAME)
def bound(files):
    t=target();paths={t['battle'],t['battle']+'.meta',t['art_dir']+'.meta'}
    return {p:s for p,s in files.items() if p in paths or p.startswith(t['art_dir']+'/')}

def reporter_stamp_ok(before,after):
    path='Assets/Reporter/Editor/ReporterEditor.cs'
    gate=HERE/'runtime_start_gate_20261029.json'
    if before.get(path)!=after.get(path) or not gate.exists():return False
    text=(ROOT/'Assets/StreamingAssets/build_info').read_text(encoding='utf-8')
    match=re.fullmatch(r'Build from '+re.escape(os.environ['COMPUTERNAME'])+r' at (\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}:\d{2})',text)
    if not match:return False
    stamp=datetime.strptime(match.group(1),'%Y/%m/%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=8)))
    start=datetime.fromisoformat(read(gate)['observed_at']).replace(microsecond=0)
    return start<=stamp<=datetime.fromisoformat(now())
def audit(files=None):
    owner();before=read(HERE/'production_paths_before_20261029.json');after=files or snapshot();t=target();changes=[];unexpected=[]
    for p in sorted(set(before)|set(after)):
        if before.get(p)==after.get(p):continue
        why='unexpected'
        if p==t['battle']:why='current battle prefab'
        elif p==t['art_dir']+'.meta' or p.startswith(t['art_dir']+'/'):why='current Directions including directory root meta'
        elif p=='Assets/StreamingAssets/build_info' and reporter_stamp_ok(before,after):why='unchanged ReporterEditor initialization after actual Play domain reload; exact device and local timestamp within run window'
        row={'path':p,'before':before.get(p),'after':after.get(p),'attribution':why};changes.append(row)
        if why=='unexpected':unexpected.append(row)
    six={p:{'before':s,'after':after.get(p),'matches':after.get(p)==s} for p,s in read(HERE/'sync_start_20261029.json')['protected_six'].items()}
    protected=all(v['matches'] for p,v in six.items() if p!=t['battle'])
    code=(RUN.parent/'Batch01_10/audit_scope.py').read_text(encoding='utf-8')
    ns={'HERE':RUN,'ROOT':ROOT,'targets':{NAME:t},'re':re,'hashlib':hashlib}
    exec(code[code.index('def sha('):code.index('changed=[];unexpected=[]')],ns)
    semantic=ns['semantic'](NAME)
    # Keep the unchanged generic semantic report, including its failure. Only the
    # recorded empty-expression-array repair on THIS prefab has a separate gate.
    binding_repair={'applies':False,'pass':False}
    repair_file=HERE/'head_binding_repair_r02_20261029.json'
    if repair_file.exists() and not semantic['pass']:
        repair=read(repair_file)
        a=ns['blocks']((HERE/'reference'/('Enemy_'+NAME+'.prefab')).read_text(encoding='utf-8-sig'))
        b=ns['blocks']((ROOT/t['battle']).read_text(encoding='utf-8-sig'))
        failures=semantic['unexpected']
        assert len(failures)==1 and set(failures[0])=={'original_component_changed','kind','owner'},failures
        component=failures[0]['original_component_changed']
        assert failures[0]['kind']==114
        old=a[component]['text'];current=b[component]['text']
        assert 'guid: 0b0e843e89b70624f84c1a3dca9dc65b' in old
        pattern=r'^  HeadSprites:(?: \[\])?\n(?:  - \{[^\n]+\}\n)*'
        old_match=re.search(pattern,old,re.M);new_match=re.search(pattern,current,re.M)
        assert old_match and new_match and old_match[0]=='  HeadSprites: []\n'
        refs=repair['result']['bindings']
        assert [r['name'] for r in refs]==['HeadNormal','HeadAngry','HeadDead']
        atlas_guid=re.search(r'^guid: (\w+)',(ROOT/(t['atlas']+'.meta')).read_text(encoding='utf-8'),re.M)[1]
        assert all(r['guid']==atlas_guid and r['path']==t['atlas'] for r in refs)
        expected='  HeadSprites:\n'+''.join('  - {fileID: '+str(r['fileID'])+', guid: '+r['guid']+', type: 3}\n' for r in refs)
        assert new_match[0]==expected,(new_match[0],expected)
        assert ns['canonical'](re.sub(pattern,'  HeadSprites: PRECISE_RECORDED_REPAIR\n',old,flags=re.M))==ns['canonical'](re.sub(pattern,'  HeadSprites: PRECISE_RECORDED_REPAIR\n',current,flags=re.M))
        assert sha(ROOT/t['battle'])==repair['after_prefab_sha256']
        binding_repair={'applies':True,'pass':True,'component':component,'before':'empty expression array','after':refs,'repair_manifest_sha256':sha(repair_file),
                        'reason':'Fill only this originally empty expression array with three unchanged original-atlas sprites. Generic semantic failure retained verbatim; all other original fields pass its unchanged comparison.'}
    scoped_semantic_pass=semantic['pass'] or binding_repair['pass']
    return {'observed_at':now(),'method':'Current-character complete path union and SHA256, includes additions/deletions; original semantic comparison reused.',
            'before_count':len(before),'after_count':len(after),'changes':changes,'added':sum(x['before'] is None for x in changes),'deleted':sum(x['after'] is None for x in changes),
            'unexpected':unexpected,'protected_six':six,'protected_sources_and_meta_ok':protected,'prefab_semantic':semantic,
            'head_binding_repair':binding_repair,'prefab_semantic_scoped_pass':scoped_semantic_pass,
            'pass':not unexpected and protected and scoped_semantic_pass,'legacy_global_scope':'Historical failures not re-audited or reclassified. Generic original-component comparison retained, including this character expression-array repair difference.'}
