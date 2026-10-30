"""Prepare once and render the battle reference without replacing shared contact evidence."""
from pathlib import Path
import hashlib, json, os, subprocess, sys

D = Path(__file__).resolve().parent
HERE = D.parent
chain = json.loads((HERE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state'] == 'active' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == D.name
assert chain['dispatch_token'] == 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
assert not (D/'anatomy_plan.json').exists() and not (D/'generation').exists(), 'Preparation already exists; resume it'
assert not (D/'reference/battle_prefab_offline.png').exists()
subprocess.run([sys.executable,'-X','utf8',str(HERE/'prepare_character.py'),D.name],check=True)

renderer = HERE/'render_source_reference.py'
source = renderer.read_text(encoding='utf-8')
original = "contact.save(HERE/'source_reference_contact.png')"
assert source.count(original) == 1
source = source.replace(original, "contact.save(HERE/'ShardLizard/reference/battle_contact.png')")
saved_argv = sys.argv
try:
    sys.argv = [str(renderer),'--battle','--name',D.name]
    exec(compile(source,str(renderer),'exec'),{'__file__':str(renderer),'__name__':'__main__'})
finally:
    sys.argv = saved_argv
(D/'reference/render_method.json').write_text(json.dumps(dict(
    method='Existing offline serialized-prefab renderer; only shared contact output redirected to character reference directory',
    renderer=str(renderer),renderer_sha256=hashlib.sha256(renderer.read_bytes()).hexdigest().upper(),
    runtime_evidence=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress = json.loads((HERE/'progress.json').read_text(encoding='utf-8'))
item = next(i for i in progress['items'] if i['name'] == D.name)
assert item['status'] == 'not_started'
item['status'] = 'reference_prepared'
progress['current'] = D.name
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
