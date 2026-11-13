import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = StdioServerParameters(
        command=os.path.expandvars(r"%USERPROFILE%\.local\bin\uvx.exe"),
        args=["--from", "mcpforunityserver==10.3.0", "mcp-for-unity", "--transport", "stdio"],
        env={**os.environ, "UNITY_MCP_PORT": "6400"},
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            command = sys.argv[1]
            if command == "resources":
                resources = await session.list_resources()
                print(json.dumps([r.model_dump(mode="json") for r in resources.resources], ensure_ascii=False, indent=2))
            elif command == "tools":
                tools = await session.list_tools()
                print(json.dumps([t.model_dump(mode="json") for t in tools.tools], ensure_ascii=False, indent=2))
            elif command == "toolinfo":
                tools = await session.list_tools()
                wanted = set(sys.argv[2:])
                print(json.dumps([t.model_dump(mode="json") for t in tools.tools if t.name in wanted], ensure_ascii=False, indent=2))
            elif command == "read":
                result = await session.read_resource(sys.argv[2])
                print(json.dumps([c.model_dump() for c in result.contents], ensure_ascii=False, indent=2))
            elif command == "identity":
                try:
                    custom = await session.read_resource("mcpforunity://custom-tools")
                    print("CUSTOM_TOOLS=" + "\n".join(getattr(c, "text", "") for c in custom.contents))
                except Exception as exc:
                    print(f"CUSTOM_TOOLS_UNAVAILABLE={type(exc).__name__}: {exc}")
                instances = await session.read_resource("mcpforunity://instances")
                print("INSTANCES=" + "\n".join(getattr(c, "text", "") for c in instances.contents))
                selected = await session.call_tool("set_active_instance", {"instance": "6400"})
                print("SET_ACTIVE_INSTANCE=" + json.dumps(selected.model_dump(mode="json"), ensure_ascii=False))
                info = await session.read_resource("mcpforunity://project/info")
                print("PROJECT_INFO=" + "\n".join(getattr(c, "text", "") for c in info.contents))
            elif command == "call":
                await session.call_tool("set_active_instance", {"instance": "6400"})
                result = await session.call_tool(sys.argv[2], json.loads(sys.argv[3]))
                print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
            elif command == "state":
                await session.call_tool("set_active_instance", {"instance": "6400"})
                result = await session.read_resource("mcpforunity://editor/state")
                print("\n".join(getattr(c, "text", "") for c in result.contents))
            else:
                raise ValueError(f"Unknown command: {command}")


asyncio.run(main())
