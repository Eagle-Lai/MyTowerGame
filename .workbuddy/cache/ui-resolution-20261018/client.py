import asyncio, json, sys, os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path('D:/FreedomTower_1')
async def run(session):
    await session.initialize()
    for uri in ['mcpforunity://custom-tools','mcpforunity://instances']:
        try:
            result = await session.read_resource(uri)
        except Exception as ex:
            print('RESOURCE_UNAVAILABLE',uri,str(ex),flush=True)
            if uri.endswith('instances'):raise
            continue
        print(uri, result.model_dump_json(), flush=True)
        if uri.endswith('instances'):
            raw = json.loads(result.contents[0].text)
    instances = raw.get('data',{}).get('instances', raw.get('instances',[]))
    print('INSTANCE_DATA',json.dumps(raw),flush=True)
    if sys.argv[2] == 'discover':
        ts=await session.list_tools()
        Path('.workbuddy/cache/ui-resolution-20261018/tools.json').write_text(ts.model_dump_json(),encoding='utf-8')
        for t in ts.tools:
            if t.name in ['execute_code','refresh_unity','manage_editor','read_console','manage_tools']:print(t.model_dump_json(),flush=True)
        return
    matches=[x for x in instances if str(x.get('path','')).replace('\\','/').lower() in ['d:/freedomtower_1/assets','d:/freedomtower_1'] or (not x.get('path') and x.get('name')=='FreedomTower_1')]
    if len(matches)!=1:raise RuntimeError('Expected exactly one matching project instance')
    instance = matches[0]['id']
    print((await session.call_tool('set_active_instance', {'instance':instance})).model_dump_json(),flush=True)
    info = await session.read_resource('mcpforunity://project/info')
    print('PROJECT',info.model_dump_json(),flush=True)
    data = json.loads(info.contents[0].text).get('data',{})
    if str(data.get('projectRoot','')).replace('\\','/').rstrip('/').lower() != str(ROOT).replace('\\','/').lower():
        raise RuntimeError('Project identity mismatch: '+str(data))
    action=sys.argv[2]
    if action == 'audit':
        print((await session.call_tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})).model_dump_json(),flush=True)
        print((await session.read_resource('mcpforunity://editor/state')).model_dump_json(),flush=True)
    elif action == 'read':
        print((await session.read_resource(sys.argv[4])).model_dump_json(),flush=True)
    elif action == 'batch':
        await session.call_tool('manage_tools',{'action':'activate','group':'scripting_ext'})
        calls=json.loads(Path(sys.argv[4]).read_text(encoding='utf-8-sig'))
        for call in calls:
            result=await session.call_tool(call['name'],call['arguments'])
            print(call.get('label',call['name']),result.model_dump_json(),flush=True)
            if result.isError:raise RuntimeError('MCP batch call failed')
            data=result.structuredContent
            if data and data.get('success') is False:raise RuntimeError('Unity tool reported failure: '+str(data))
    else:
        args=json.loads(Path(sys.argv[4]).read_text(encoding='utf-8-sig')) if len(sys.argv)>4 else {}
        if action=='execute_code':
            print((await session.call_tool('manage_tools',{'action':'activate','group':'scripting_ext'})).model_dump_json(),flush=True)
        print((await session.call_tool(action,args)).model_dump_json(),flush=True)

async def main():
    if sys.argv[1]=='stdio':
        params=StdioServerParameters(command=sys.executable,args=['-m','mcp_for_unity','--transport','stdio'])
        # Use the installed entry point, without downloading another server.
        params.args=[str(Path(sys.executable).parent/'mcp-for-unity.exe'),'--transport','stdio']
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session: await run(session)
    else:
        import httpx
        async with streamablehttp_client('http://127.0.0.1:8082/mcp', httpx_client_factory=lambda **kw:httpx.AsyncClient(**{**kw,'trust_env':False})) as (r,w,_):
            async with ClientSession(r,w) as session: await run(session)
if __name__=='__main__':asyncio.run(main())
