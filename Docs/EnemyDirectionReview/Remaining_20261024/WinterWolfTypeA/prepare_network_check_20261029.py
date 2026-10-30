from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
RUN=HERE.parent
chain=json.loads((RUN/'conversation_chain.json').read_text(encoding='utf-8'))
text=(RUN/'WinterWarg/read_only_service_recheck_20261029.mjs').read_text(encoding='utf-8')
text=text.replace('01a186cb-e01e-72b2-ad8b-f5a5b86bfd1f',chain['owner_thread_id']).replace('winterogre-to-winterwarg-20261029_163224-4c489e91-3117-4716-a1e2-87af74077d40',chain['dispatch_token']).replace("character:'WinterWarg'","character:'WinterWolfTypeA'")
path=HERE/'read_only_service_recheck_20261029.mjs'
assert not path.exists()
path.write_text(text,encoding='utf-8')
shutil.copy2(RUN/'generate.mjs',HERE/'generate_before_current_recovery_20261029.mjs')
