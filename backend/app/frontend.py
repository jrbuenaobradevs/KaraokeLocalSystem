from pathlib import Path
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent

server_dashboard_path = BASE_DIR / 'frontend' / 'server-dashboard' / 'dist'
client_ui_path = BASE_DIR / 'frontend' / 'client-ui' / 'dist'


def mount_frontend(app):
    if server_dashboard_path.exists():
        app.mount('/dashboard', StaticFiles(directory=server_dashboard_path), name='server-dashboard')
    if client_ui_path.exists():
        app.mount('/app', StaticFiles(directory=client_ui_path), name='client-ui')
