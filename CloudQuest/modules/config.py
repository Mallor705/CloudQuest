# modules/config.py
# CONFIGURAÇÃO DE LOG (UTF-8)
# ====================================================
import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Determina o diretório do script e o diretório raiz do projeto
script_dir = Path(__file__).parent
cloud_quest_root = script_dir.parent.parent  # Ajusta para o diretório raiz do projeto
log_dir = cloud_quest_root / "logs"
log_path = log_dir / "CloudQuest.log"

# Cria o diretório de logs se não existir
if not log_dir.exists():
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Diretório de logs criado: {log_dir}")

def write_log(message, level='Info'):
    """
    Escreve mensagem no arquivo de log
    :param message: Mensagem a ser registrada
    :param level: Nível do log (Info, Warning, Error)
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    # Certifica-se de que o diretório de logs existe
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_entry + '\n')
    except Exception as e:
        print(f"Erro ao escrever no log: {str(e)}")

# Inicializa o arquivo de log (cria ou acrescenta)
def init_log():
    """Inicializa o arquivo de log para uma nova sessão"""
    log_header = f"=== [ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ] Sessão iniciada ===\n"
    
    try:
        with open(log_path, 'a', encoding='utf-8') as log_file:
            log_file.write(log_header)
    except Exception as e:
        print(f"Erro ao inicializar o log: {str(e)}")

def load_config():
    """
    Carrega a configuração do perfil do usuário
    :return: Dicionário com a configuração
    """
    try:
        # Lê o nome do perfil do arquivo temporário
        temp_file = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")
        with open(temp_file, 'r') as f:
            profile_name = f.read().strip()
        
        write_log(f"Perfil recebido: '{profile_name}'")
        
        if not profile_name:
            write_log("Nenhum perfil foi especificado.", "Error")
            raise ValueError("Erro: Nome do perfil ausente.")
        
        # Constrói o caminho para o arquivo de configuração
        profiles_dir = cloud_quest_root / "profiles"
        config_path = profiles_dir / f"{profile_name}.json"
        
        write_log(f"Procurando perfil em: {config_path}", "Info")
        
        if not config_path.exists():
            write_log("Arquivo de configuração do usuário não encontrado.", "Warning")
            raise FileNotFoundError("Arquivo de configuração do usuário não encontrado.")
        
        # Carrega o JSON de configuração
        with open(config_path, 'r', encoding='utf-8') as config_file:
            user_config = json.load(config_file)
        
        # Converte os nomes das chaves para snake_case para seguir as convenções Python
        config = {
            'rclone_path': user_config['RclonePath'],
            'cloud_remote': user_config['CloudRemote'],
            'cloud_dir': user_config['CloudDir'],
            'local_dir': user_config['LocalDir'],
            'game_process': user_config['GameProcess'],
            'game_name': user_config['GameName'],
            'launcher_exe_path': user_config['ExecutablePath']
        }
        
        return config
    
    except Exception as e:
        write_log(f"Erro ao carregar configuração: {str(e)}", "Error")
        raise

# Inicializa o log quando o módulo é importado
init_log()