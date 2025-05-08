#!/usr/bin/env python3
# CloudQuest - Configurações globais

import os
import sys
import tempfile
from pathlib import Path

# Diretórios do projeto
BASE_DIR = Path(__file__).resolve().parent.parent  # cloudquest/
LOGS_DIR = BASE_DIR / "logs"
PROFILES_DIR = BASE_DIR / "config" / "profiles"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"

# Criação de diretórios necessários
LOGS_DIR.mkdir(exist_ok=True)
PROFILES_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
ICONS_DIR.mkdir(exist_ok=True)

# Arquivo de log
LOG_FILE = LOGS_DIR / "CloudQuest.log"

# Arquivo temporário para perfil (usado pelo launcher .bat)
TEMP_PROFILE_FILE = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")

# Configurações do Rclone
RCLONE_TIMEOUT = 120  # segundos
RCLONE_MAX_RETRIES = 3
RCLONE_RETRY_WAIT = 5  # segundos

# Configurações de notificação
NOTIFICATION_DISPLAY_TIME = 5000  # milissegundos
NOTIFICATION_WIDTH = 300
NOTIFICATION_HEIGHT = 75

# Configurações padrão (podem ser sobrescritas pelos perfis)
DEFAULT_FONT = "Segoe UI"  # Fallback se Montserrat não estiver disponível

# Cores da UI
COLORS = {
    "background": (28, 32, 39),  # RGB
    "dark_bg": (17, 23, 30),
    "text_primary": (255, 255, 255),
    "text_secondary": (140, 145, 151),
    "error": (220, 50, 50),
}