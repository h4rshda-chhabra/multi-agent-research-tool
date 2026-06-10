import requests, json
url = 'http://localhost:8001/api/v1/auth/register'
payload = {"name": "Test User", "email": "test@example.com", "password": "password123"}
headers = {'Content-Type': 'application/json'}
resp = requests.post(url, json=payload, headers=headers)
print('Status:', resp.status_code)
print('Body:', resp.text)
