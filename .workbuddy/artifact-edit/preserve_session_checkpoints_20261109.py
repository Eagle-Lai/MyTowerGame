"""Preserve this session's isolated replay checkpoints, never historical player saves."""
import json,sqlite3,time,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'Library/BalanceStage/trusted-terminal-design-20261109/engine'/sys.argv[1]
SOURCE=Path(sys.argv[2])
assert re.fullmatch(r'replay-[0-9a-f]{32}',SOURCE.parent.name)
destination=RUN/'checkpoints';destination.mkdir(exist_ok=True)
seen=set()
for _ in range(3600):
    try:
        state=json.loads((RUN/'status.json').read_text(encoding='utf-8-sig'))
        if state.get('completed',0)>0:break
        wave=state.get('round',0)
        if wave not in seen and SOURCE.exists():
            target=destination/f'at-W{wave:02d}.db'
            with sqlite3.connect(f'file:{SOURCE.as_posix()}?mode=ro',uri=True,timeout=2) as src:
                with sqlite3.connect(target) as dst:src.backup(dst)
            seen.add(wave)
            print(f'Preserved current-session checkpoint observed at W{wave}',flush=True)
        if state.get('phase') in ('complete','exception','cancelled','batch_timeout'):break
    except (OSError,ValueError,sqlite3.Error):pass
    time.sleep(1)
