"""极简 Unity MCP 客户端（Streamable HTTP + SSE）。"""
import json, urllib.request

URL = 'http://127.0.0.1:8082/mcp'
_sid = [None]
_id = [0]


def _rpc(method, params=None, notify=False):
    _id[0] += 1
    payload = {'jsonrpc': '2.0', 'method': method}
    if not notify:
        payload['id'] = _id[0]
    if params is not None:
        payload['params'] = params
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    })
    if _sid[0]:
        req.add_header('mcp-session-id', _sid[0])
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode('utf-8', 'ignore')
        if r.headers.get('mcp-session-id'):
            _sid[0] = r.headers['mcp-session-id']
    for line in body.splitlines():
        if line.startswith('data: '):
            return json.loads(line[6:])
    return json.loads(body) if body.strip() else None


def init():
    r = _rpc('initialize', {
        'protocolVersion': '2024-11-05', 'capabilities': {},
        'clientInfo': {'name': 'wb', 'version': '1.0'}})
    _rpc('notifications/initialized', None, notify=True)
    return r


def read(uri):
    r = _rpc('resources/read', {'uri': uri})
    return r.get('result', {}).get('contents', [{}])[0].get('text', '')


def tools():
    r = _rpc('tools/list', {})
    return [t['name'] for t in r.get('result', {}).get('tools', [])]


def call(name, args):
    r = _rpc('tools/call', {'name': name, 'arguments': args})
    return r.get('result', {})
