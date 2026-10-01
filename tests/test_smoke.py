from app import create_app

def test_app_starts():
    app = create_app()
    assert app is not None

def test_auth_routes_exist():
    app = create_app()
    client = app.test_client()
    assert client.get("/login").status_code == 200
    assert client.get("/register").status_code == 200
