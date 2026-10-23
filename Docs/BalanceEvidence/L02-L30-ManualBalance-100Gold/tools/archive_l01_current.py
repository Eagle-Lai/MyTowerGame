"""Preserve this task's previous current-check before replacing its observations."""
from formal_tools import *
import sys, shutil, datetime

tag = sys.argv[1]
assert tag and all(c.isalnum() or c in '-_' for c in tag)
source = REPORT / 'L01-current-check'
assert source.is_dir()
destination = REPORT / 'audit/l01-current-history' / tag
assert not destination.exists(), destination
shutil.copytree(source, destination)
files = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in source.rglob('*') if p.is_file()}
assert files and all(hashlib.sha256((destination / p).read_bytes()).hexdigest() == h
                     for p, h in files.items())
(destination / 'archive-provenance.json').write_text(json.dumps(dict(
    capturedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source='L01-current-check', purpose='Preserve previous observations before replacement',
    files=files), ensure_ascii=False, indent=2), encoding='utf-8')
print('Previous L01 current-check preserved:', destination.relative_to(REPORT), len(files), 'files')
