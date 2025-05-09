#!/usr/bin/env python3
# CloudQuest - Configurações globais

import os
import sys
import tempfile
from pathlib import Path

# Determinar diretórios da aplicação com base no modo de execução
if getattr(sys, 'frozen', False):
    # Executando como executável empacotado (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)  # Diretório temporário do PyInstaller
    APP_DIR = Path(os.path.dirname(sys.executable))  # Diretório do executável
else:
    # Executando como script Python normal
    BASE_DIR = Path(__file__).resolve().parent.parent  # cloudquest/
    APP_DIR = BASE_DIR

# Diretórios do projeto
LOGS_DIR = APP_DIR / "logs"

if getattr(sys, 'frozen', False):
    PROFILES_DIR = APP_DIR / "profiles"  # Pasta ao lado do executável
else:
    PROFILES_DIR = BASE_DIR / "config" / "profiles"  # Modo de desenvolvimento
    
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# Criação de diretórios necessários que devem persistir (apenas no diretório APP)
LOGS_DIR.mkdir(exist_ok=True)

# Arquivo temporário para perfil
TEMP_PROFILE_FILE = os.path.join(tempfile.gettempdir(), "cloudquest_profile.txt")

# Configurações do Rclone
RCLONE_TIMEOUT = 120  # segundos
RCLONE_MAX_RETRIES = 3
RCLONE_RETRY_WAIT = 5  # segundos

# Configurações de notificação
NOTIFICATION_DISPLAY_TIME = 5000  # milissegundos
NOTIFICATION_WIDTH = 300
NOTIFICATION_HEIGHT = 75

# Configurações padrão (podem ser sobrescritas pelos perfis)
DEFAULT_FONT = "Segoe UI"

# Cores da UI
COLORS = {
    "background": (28, 32, 39),  # RGB
    "dark_bg": (17, 23, 30),
    "text_primary": (255, 255, 255),
    "text_secondary": (140, 145, 151),
    "error": (220, 50, 50),
}

# Adicione no final do settings.py
TEMP_PROFILE_PATH = Path(TEMP_PROFILE_FILE)