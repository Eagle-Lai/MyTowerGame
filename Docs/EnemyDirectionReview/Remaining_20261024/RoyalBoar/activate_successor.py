"""Complete only the acknowledged, unique handoff, then relinquish ownership."""
from serial_common import *

chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'handoff_ready'
assert chain['owner_thread_id'] == chain['parent_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == 'SabretoothTiger'
assert chain['dispatch_token'] == 'royalboar-to-sabretoothtiger-a2029bb593694bc689b95040377c6e4f'
result = read(D / 'successor_create_response.json')
assert result['isError'] is False
created = json.loads(result['content'][0]['text'])
assert created == {'threadId': '01a17878-9b2e-7bb1-a0e5-d5d089b944a5', 'hostId': 'local'}
assert not any(x['thread_id'] == created['threadId'] for x in chain['dispatch_history'])
record = dict(sequence=max(x['sequence'] for x in chain['dispatch_history']) + 1,
              character='SabretoothTiger', thread_id=created['threadId'], host_id=created['hostId'],
              dispatch_token=chain['dispatch_token'], created=True, project_association_confirmed=True,
              handoff_file=chain['last_handoff_file'], created_at=now())
write(D / 'successor_created_record.json', record)
chain['dispatch_history'].append(record)
chain.update(state='active', owner_thread_id=created['threadId'], owner_host_id=created['hostId'], activated_at=now())
write(H / 'conversation_chain.json', chain)
print(json.dumps(dict(state='active', owner_thread_id=created['threadId'], current_character=chain['current_character']), ensure_ascii=False))
