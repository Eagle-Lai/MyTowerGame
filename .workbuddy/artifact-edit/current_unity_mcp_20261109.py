"""Use the configured stdio MCP transport and MCP SDK tool calls only."""
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def display(label, result):
    print(label + '=' + json.dumps(result.model_dump(mode='json'), ensure_ascii=False), flush=True)

async def main():
    parameters = StdioServerParameters(command=os.path.expandvars(r'%USERPROFILE%\.local\bin\uvx.exe'),
        args=['--from', 'mcpforunityserver==10.3.0', 'mcp-for-unity', '--transport', 'stdio'],
        env={**os.environ, 'UNITY_MCP_PORT': '6400'})
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            try:
                display('CUSTOM_TOOLS', await session.read_resource('mcpforunity://custom-tools'))
            except Exception as exc:
                print('CUSTOM_TOOLS_RESOURCE_UNAVAILABLE=' + str(exc), flush=True)
            display('INSTANCES', await session.read_resource('mcpforunity://instances'))
            selected = await session.call_tool('set_active_instance', {'instance': 'FreedomTower_1@520e2c6d'})
            display('ACTIVE_INSTANCE', selected)
            info = await session.read_resource('mcpforunity://project/info')
            display('PROJECT_INFO', info)
            text = '\n'.join(getattr(c, 'text', '') for c in info.contents)
            if 'FreedomTower_1' not in text or '2022.3.62f3c1' not in text:
                raise RuntimeError('Current project identity was not confirmed')
            if len(sys.argv) > 1 and sys.argv[1] == 'toolinfo':
                wanted = set(sys.argv[2:])
                catalog = await session.list_tools()
                print(json.dumps([t.model_dump(mode='json') for t in catalog.tools if t.name in wanted], ensure_ascii=False))
            elif len(sys.argv) > 1 and sys.argv[1] == 'call':
                args = json.loads(open(sys.argv[3], encoding='utf-8').read())
                display('RESULT', await session.call_tool(sys.argv[2], args))
            elif len(sys.argv) > 1 and sys.argv[1] == 'serve':
                directory = Path(sys.argv[2]); directory.mkdir(parents=True, exist_ok=True)
                (directory / 'ready.json').write_text(text, encoding='utf-8')
                while not (directory / 'stop').exists():
                    for request in sorted(directory.glob('*.request.json')):
                        response = request.with_name(request.name.replace('.request.json', '.response.json'))
                        if response.exists():
                            continue
                        obj = json.loads(request.read_text(encoding='utf-8'))
                        try:
                            if obj['tool'] == '__resource__':
                                result = await session.read_resource(obj['args']['uri'])
                            else:
                                result = await session.call_tool(obj['tool'], obj.get('args', {}))
                            response.write_text(json.dumps(result.model_dump(mode='json'), ensure_ascii=False), encoding='utf-8')
                        except Exception as exc:
                            response.write_text(json.dumps({'bridgeError': str(exc)}, ensure_ascii=False), encoding='utf-8')
                            raise
                    await asyncio.sleep(.2)
            else:
                display('EDITOR_STATE', await session.read_resource('mcpforunity://editor/state'))

asyncio.run(main())
