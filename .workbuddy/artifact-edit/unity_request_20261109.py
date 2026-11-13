import json
import sys
import time
from pathlib import Path
root=Path(__file__).resolve().parents[2]
directory=root/'Library/BalanceStage/unity-mcp-20261109'
name=str(time.time_ns())
request=directory/(name+'.request.json')
response=directory/(name+'.response.json')
args=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')) if len(sys.argv)>2 else {}
temp=request.with_suffix('.tmp')
temp.write_text(json.dumps({'tool':sys.argv[1],'args':args},ensure_ascii=False),encoding='utf-8')
temp.replace(request)
start=time.monotonic()
while time.monotonic()-start<55:
 if response.exists():
  text=response.read_text(encoding='utf-8')
  print(text)
  sys.exit(0)
 time.sleep(.15)
raise TimeoutError('MCP tool response not received; do not retry before checking current bridge and instance')
