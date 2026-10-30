"""Use the project's existing HTTP MCP endpoint directly when the desktop client's handshake fails.
No proxy is used for loopback. Every invocation discovers and checks the Unity identity.
Usage: mcp_call.py request.json. Requests and full responses remain under Docs.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, os, sys, urllib.request, uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# 2026-10-28: the user moved MyTowerGame to 8088; 8082 hosts another project.
URL = os.environ.get('MYTOWERGAME_MCP_URL', 'http://127.0.0.1:8088/mcp')

class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.session = None
        self.history = []
        self.rpc('initialize', {'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'MyTowerGame-direction-review','version':'1.0'}})
        self.rpc('notifications/initialized', {}, notify=True)

    def rpc(self, method, params, notify=False):
        payload = {'jsonrpc':'2.0','method':method,'params':params}
        if not notify: payload['id'] = str(uuid.uuid4())
        headers = {'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.session: headers['Mcp-Session-Id'] = self.session
        request = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=headers, method='POST')
        with self.opener.open(request, timeout=150) as response:
            self.session = response.headers.get('Mcp-Session-Id') or self.session
            raw = response.read().decode('utf-8')
        if not raw.strip(): return None
        if raw.lstrip().startswith('{'): result = json.loads(raw)
        else:
            events = [json.loads(line[5:].strip()) for line in raw.splitlines() if line.startswith('data:')]
            result = next((event for event in events if event.get('id') == payload.get('id')), events[-1])
        self.history.append({'method':method,'params':params,'response':result})
        if 'error' in result: raise RuntimeError(json.dumps(result['error'], ensure_ascii=False))
        return result.get('result')

    def resource(self, uri):
        result = self.rpc('resources/read', {'uri':uri})
        return json.loads(result['contents'][0]['text'])

    def tool(self, name, arguments):
        result = self.rpc('tools/call', {'name':name,'arguments':arguments})
        if result.get('isError'): raise RuntimeError(json.dumps(result,ensure_ascii=False))
        return result

    def identity(self):
        self.resource('mcpforunity://custom-tools')
        instances = self.resource('mcpforunity://instances')
        listing = instances.get('data',instances).get('instances',[])
        targets = [item for item in listing if item.get('name') == 'MyTowerGame']
        if len(targets) != 1: raise RuntimeError('Expected exactly one MyTowerGame instance: '+str(instances))
        self.tool('set_active_instance', {'instance':targets[0]['id']})
        project = self.resource('mcpforunity://project/info')['data']
        version = (ROOT/'ProjectSettings/ProjectVersion.txt').read_text().splitlines()[0].split(':',1)[1].strip()
        if project['projectRoot'].replace('\\','/').rstrip('/').lower() != str(ROOT).replace('\\','/').lower() or project['unityVersion'] != version:
            raise RuntimeError('Project identity mismatch: '+str(project))
        return project

if __name__ == '__main__':
    request_path = Path(sys.argv[1]).resolve()
    request = json.loads(request_path.read_text(encoding='utf-8-sig'))
    client = None
    report = {'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'transport':URL,'request_file':str(request_path)}
    try:
        client = Client()
        report['project'] = client.identity()
        report['results'] = []
        for action in request['actions']:
            if action['method'] == 'resource': value = client.resource(action['uri'])
            elif action['method'] == 'tools/list': value = client.rpc('tools/list',{})
            else: value = client.tool(action['name'], action.get('arguments',{}))
            report['results'].append(value)
        report['success'] = True
    except Exception as error:
        report.update(success=False,error=str(error))
    report['protocol_history'] = client.history if client else []
    output = request_path.with_name(request_path.stem+'_response.json')
    if output.exists():
        output = request_path.with_name(request_path.stem+'_response_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.json')
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary = {k:v for k,v in report.items() if k not in ['protocol_history','results']}
    summary['response_file'] = str(output)
    summary['results'] = [{'tools':[t['name'] for t in v['tools']]} if isinstance(v,dict) and 'tools' in v else v for v in report.get('results',[])]
    print(json.dumps(summary,ensure_ascii=False))
    if not report['success']: raise SystemExit(1)
