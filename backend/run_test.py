import httpx, json, sys

with open('token.txt') as f:
    token = f.read().strip()

headers = {'Authorization': f'Bearer {token}'}

topic = sys.argv[1] if len(sys.argv) > 1 else 'Recent advances in large language model reasoning capabilities'

r = httpx.post('http://localhost:8000/api/v1/research',
    json={'topic': topic},
    headers=headers)
print(f'Research: {r.status_code}')
data = r.json()
report_id = data.get('report_id', '')
print(f'Report ID: {report_id}')

if not report_id:
    print(f'Error: {data}')
    sys.exit(1)

with httpx.stream('GET', f'http://localhost:8000/api/v1/research/{report_id}/stream', headers=headers, timeout=120) as resp:
    for line in resp.iter_lines():
        if line.startswith('data: '):
            event = json.loads(line[6:])
            msg = event.get('message', '')
            agent = event.get('agent', '')
            etype = event.get('type', '?')
            if agent:
                print(f'  [{etype}] {agent}: {msg}')
            else:
                print(f'  [{etype}] {msg}')
            if event.get('type') in ('complete', 'error'):
                if event.get('type') == 'complete':
                    print('\n=== RESEARCH COMPLETE ===')
                else:
                    print(f'\n=== ERROR: {event.get("message")} ===')
                break
