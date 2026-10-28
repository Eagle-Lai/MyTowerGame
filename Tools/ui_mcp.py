"""Task-scoped MCP client. Never route FishTestGame commands through another project."""
import asyncio
import json
import sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def main():
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    async with streamable_http_client('http://127.0.0.1:8084/mcp') as streams:
        reader, writer = streams[:2]
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            await session.read_resource('mcpforunity://custom-tools')
            instances = json.loads((await session.read_resource('mcpforunity://instances')).contents[0].text)
            candidates = [x for x in instances.get('instances', []) if x['name'] == 'FishTestGame']
            if len(candidates) != 1:
                raise RuntimeError('Expected one FishTestGame instance on port 8084: ' + str(instances))
            await session.call_tool('set_active_instance', {'instance': candidates[0]['id']})
            info = json.loads((await session.read_resource('mcpforunity://project/info')).contents[0].text)
            project = info['data']
            if project['projectRoot'].replace('\\', '/').lower().rstrip('/') != 'd:/fishtestgame':
                raise RuntimeError('Wrong Unity project: ' + str(project))
            version = (Path(__file__).resolve().parents[1] / 'ProjectSettings/ProjectVersion.txt').read_text(encoding='utf-8-sig').splitlines()[0].split(':', 1)[1].strip()
            if project['unityVersion'] != version:
                raise RuntimeError('Unity version differs from ProjectVersion.txt: ' + str(project))
            print(json.dumps({'identity': project, 'instance': candidates[0]['id'], 'port': 8084}, ensure_ascii=False))
            for action in request:
                if 'resource' in action:
                    result = await session.read_resource(action['resource'])
                else:
                    result = await session.call_tool(action['tool'], action.get('arguments', {}))
                print(result.model_dump_json())

if __name__ == '__main__':
    asyncio.run(main())
