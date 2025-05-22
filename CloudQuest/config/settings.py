#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# CloudQuest - Configuracoes globais

"""
Configuracoes globais do CloudQuest.
"""

from CloudQuest.utils.paths import APP_PATHS

# Exportar caminhos da aplicacao
BASE_DIR = APP_PATHS['BASE_DIR']
APP_DIR = APP_PATHS['APP_DIR'] 
LOGS_DIR = APP_PATHS['LOGS_DIR']
PROFILES_DIR = APP_PATHS['PROFILES_DIR']
ASSETS_DIR = APP_PATHS['ASSETS_DIR']
ICONS_DIR = APP_PATHS['ICONS_DIR']
TEMP_PROFILE_FILE = APP_PATHS['TEMP_PROFILE_FILE']
TEMP_PROFILE_PATH = TEMP_PROFILE_FILE

# Configuracoes do Rclone
RCLONE_TIMEOUT = 120  # segundos
RCLONE_MAX_RETRIES = 3
RCLONE_RETRY_WAIT = 5  # segundos

# Configuracoes de notificacao
NOTIFICATION_DISPLAY_TIME = 5000  # milissegundos
NOTIFICATION_WIDTH = 300
NOTIFICATION_HEIGHT = 100

# Configuracoes padrao (podem ser sobrescritas pelos perfis)
DEFAULT_FONT = "Segoe UI"

# Cores da UI
COLORS = {
    "background": (28, 32, 39),  # RGB
    "dark_bg": (17, 23, 30),
    "text_primary": (255, 255, 255),
    "text_secondary": (140, 145, 151),
    "error": (220, 50, 50),
}