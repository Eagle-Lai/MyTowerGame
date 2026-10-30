from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
name,direction,revision,note=sys.argv[1:5]
folder=HERE/name/'generation'/direction
target=folder/revision
if target.exists():raise ValueError('Revision already exists')
target.mkdir()
(target/'prompt.txt').write_text((folder/'prompt.txt').read_text(encoding='utf-8')+'\nTargeted correction: Image 3 is the initial draft. '+note,encoding='utf-8')
