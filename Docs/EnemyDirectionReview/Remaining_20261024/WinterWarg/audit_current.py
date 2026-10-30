from session_winterwarg import *
import re

def audit():
    owner()
    baseline=read(D/'incremental_before_20261029.json')
    before=baseline['files'];after=snapshot();t=baseline['target']
    changes=[];unexpected=[]
    for p in sorted(set(before)|set(after)):
        if before.get(p)==after.get(p): continue
        role='unexpected'
        if p==t['battle']: role='current character battle prefab'
        elif p==t['art_dir']+'.meta' or p.startswith(t['art_dir']+'/'): role='current character Directions including directory root meta'
        elif p=='Assets/StreamingAssets/build_info' and after.get('Assets/Reporter/Editor/ReporterEditor.cs')==before.get('Assets/Reporter/Editor/ReporterEditor.cs') and (ROOT/p).exists() and re.fullmatch(r'Build from .+ at .+', (ROOT/p).read_text(encoding='utf-8')):
            role='unchanged ReporterEditor automatic Play timestamp'
        entry={'path':p,'before':before.get(p),'after':after.get(p),'attribution':role}
        changes.append(entry)
        if role=='unexpected': unexpected.append(entry)
    installed=(D/'installed_manifest.json').exists()
    protected={p:{'before':s,'after':after.get(p),'matches':after.get(p)==s} for p,s in baseline['protected_six'].items()}
    semantic=None
    if installed:
        original=H.parent/'Batch01_10/audit_scope.py'
        code=original.read_text(encoding='utf-8')
        definitions=code[code.index('def sha('):code.index('changed=[];unexpected=[]')]
        ns={'HERE':H,'ROOT':ROOT,'targets':{v['name']:v for v in read(H/'local_baseline.json')['targets']},'re':re,'hashlib':hashlib}
        exec(definitions,ns)
        semantic=ns['semantic'](NAME)
    protected_ok=all(v['matches'] for p,v in protected.items() if not (installed and p==t['battle']))
    return {'observed_at':now(),'basis':'Current-disk baseline and complete union of Assets/Packages/ProjectSettings/Luban, including additions/deletions; never Git HEAD.',
            'before_count':len(before),'after_count':len(after),'changes':changes,'added':sum(x['before'] is None for x in changes),'deleted':sum(x['after'] is None for x in changes),'unexpected':unexpected,
            'protected_six':protected,'protected_sources_and_meta_ok':protected_ok,'prefab_semantic':semantic,
            'pass':not unexpected and protected_ok and (semantic is None or semantic['pass']),
            'legacy_global_audit':'Historical global failures were not re-audited; this report makes only a current WinterWarg incremental claim.'}

if __name__=='__main__':
    report=audit();out=D/sys.argv[1];write(out,report,True)
    print(json.dumps({k:report[k] for k in ['before_count','after_count','added','deleted','unexpected','pass']},ensure_ascii=False))
