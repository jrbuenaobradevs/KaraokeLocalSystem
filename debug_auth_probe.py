from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
login_response = client.post('/auth/login', json={'pin': '1234'})
print('login status:', login_response.status_code)
print('set-cookie header:', login_response.headers.get('set-cookie'))
print('client cookies:', list(client.cookies.items()))
status_response = client.get('/auth/status')
print('status status:', status_response.status_code)
print('status json:', status_response.json())
print('client cookies after status:', list(client.cookies.items()))
