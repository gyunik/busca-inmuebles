import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / 'inmuebles.db'
DATABASE_URL = f'sqlite:///{DB_PATH}'

APP_TITLE = 'Buscador de Inmuebles Multicanal'
APP_VERSION = '1.0.0'
