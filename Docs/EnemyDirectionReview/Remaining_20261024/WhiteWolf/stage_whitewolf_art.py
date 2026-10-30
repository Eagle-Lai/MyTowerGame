"""WhiteWolf-only staging; keep the original generated and initial packed evidence."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
D=Path(__file__).resolve().parent; H=D.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json')
assert c['state']=='active' and c['current_character']=='WhiteWolf'
assert c['owner_thread_id']==os.environ['CODEX_THREAD_ID']=='01a183d9-2ad7-73d2-b736-3057ef92f215'
assert c['dispatch_token']=='watchdog-to-whitewolf-20261029_024758-616f3dd3-f8a9-4ec4-b44b-f70f383f1fbf'
assert not (D/'installed_manifest.json').exists()
selection={'Up':'generation/Up/revision_01/raw.png','Down':'generation/Down/revision_01/raw.png'}
assert all((D/p).is_file() for p in selection.values())
assert not (D/'staged_art').exists()
(D/'art_selection.json').write_text(json.dumps(selection,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(H/'character_step.py'),'stage','WhiteWolf'],check=True)
shutil.copytree(D/'staged_art',D/'staged_art_r01')
for f in ['parts_clean.png','offline_rig_proof.png','offline_Up.png','offline_Down.png']:
    shutil.copy2(D/f,D/('r01_'+f))
(D/'staged_art_r01/manifest.json').write_text(json.dumps({'revision':'art_r01','raw':{p:sha(D/p) for p in selection.values()},'final_art':{p.name:sha(p) for p in (D/'staged_art').iterdir() if p.is_file()}},indent=2)+'\n',encoding='utf-8')
