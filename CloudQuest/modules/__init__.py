# modules/__init__.py
# Inicialização do pacote de módulos
# ====================================================

# Expõe funções e classes principais para facilitar importações
from .config import load_config, write_log, init_log
from .notifications import NotificationWindow, show_custom_notification
from .rclone import test_rclone_config, invoke_rclone_command, set_config

# Opcional: Inicializações gerais (se necessário)
init_log()  # Inicializa o log ao importar o pacote

# Define quais símbolos são exportados quando usamos 'from modules import *'
__all__ = [
    'load_config',
    'write_log',
    'init_log',
    'NotificationWindow',
    'show_custom_notification',
    'test_rclone_config',
    'invoke_rclone_command',
    'set_config',
    'notification_queue'  # <--- Adicione esta linha
]