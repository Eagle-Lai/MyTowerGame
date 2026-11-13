"""Standard MCP SDK stdio client for the existing user-configured Unity server.

All editor access uses MCP read_resource/call_tool. No HTTP endpoint, raw Unity
socket, editor automation, source edit, or gameplay execution is implemented.
"""
import asyncio, datetime, json, os, sys, tomllib
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path('D:/FreedomTower_1')
OUT=ROOT/'Library/BalanceStage/w8-economy-apply-20261110/mcp-sdk-session'
OUT.mkdir(parents=True,exist_ok=True)
counter=0

def plain(obj):
    return obj.model_dump(mode='json',by_alias=True) if hasattr(obj,'model_dump') else obj

def record(label,result,limit=12000):
    global counter
    counter+=1
    value=plain(result)
    filename=OUT/f'{counter:03}-{label}.json'
    filename.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    preview=json.dumps(value,ensure_ascii=False)
    print(json.dumps({'record':str(filename),'result':preview[:limit],'truncated':len(preview)>limit},ensure_ascii=False),flush=True)
    return value

async def main():
    cfg=tomllib.loads(Path('C:/Users/78296/.codex/config.toml').read_text(encoding='utf-8'))['mcp_servers']['unityMCP']
    env=os.environ.copy();env.update(cfg.get('env',{}))
    params=StdioServerParameters(command=cfg['command'],args=cfg['args'],env=env,cwd=str(ROOT))
    with (OUT/'client-stderr.log').open('w',encoding='utf-8') as log:
      async with stdio_client(params,errlog=log) as (reader,writer):
        async with ClientSession(reader,writer,read_timeout_seconds=datetime.timedelta(seconds=30)) as session:
          record('initialize',await session.initialize(),4000)
          record('resources',await session.list_resources(),5000)
          # Identity workflow prescribed by the project. These are MCP resources.
          for name in ('custom-tools','instances'):
            try:record(name,await session.read_resource('mcpforunity://'+name),12000)
            except Exception as exc:record(name+'-error',{'error':str(exc)},3000)
          tools=await session.list_tools()
          file=OUT/'tools.json';file.write_text(json.dumps(plain(tools),ensure_ascii=False,indent=2),encoding='utf-8')
          print(json.dumps({'toolSchemaFile':str(file),'toolNames':[t.name for t in tools.tools]},ensure_ascii=False),flush=True)
          print('MCP_CLIENT_READY',flush=True)
          while True:
            line=await asyncio.to_thread(sys.stdin.readline)
            if not line:break
            try:
              req=json.loads(line)
              if req['op']=='exit':break
              if req['op']=='read_resource':
                result=await session.read_resource(req['uri']);label='resource'
              elif req['op']=='call_tool':
                result=await session.call_tool(req['name'],req.get('arguments',{}));label=req['name']
              elif req['op']=='list_tools':
                result=await session.list_tools();label='tools'
              else:raise ValueError('Unsupported MCP operation')
              record(label,result,req.get('maxChars',16000))
            except Exception as exc:record('request-error',{'error':str(exc)},3000)
            print('MCP_CLIENT_READY',flush=True)

if __name__=='__main__':
    asyncio.run(main())
