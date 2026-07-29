from fastapi.testclient import TestClient
from backend.app.main import app


def test_login_invalid_pin():
    client = TestClient(app)
    response = client.post('/auth/login', json={'pin': '0000'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Invalid PIN'


def test_login_valid_pin_sets_cookie():
    client = TestClient(app)
    response = client.post('/auth/login', json={'pin': '1234'})
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert response.cookies.get('karaoke_admin_token')


def test_protected_endpoint_requires_auth():
    client = TestClient(app)
    response = client.post('/queue/clear')
    assert response.status_code == 401
    assert response.json()['detail'] == 'Unauthorized'


def test_auth_status_after_login():
    client = TestClient(app)
    response = client.post('/auth/login', json={'pin': '1234'})
    assert response.status_code == 200
    status_response = client.get('/auth/status')
    assert status_response.status_code == 200
    assert status_response.json() == {'authenticated': True}
