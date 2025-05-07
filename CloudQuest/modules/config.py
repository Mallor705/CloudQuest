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
cloud_quest_root = script_dir.parent  # Ajuste: considerando que 'modules' está diretamente sob o raiz
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
        
        # Também exibe mensagens de erro no console durante desenvolvimento
        if level == 'Error':
            print(f"ERRO: {message}")
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

def get_profile_from_args():
    """
    Obtém o nome do perfil a partir dos argumentos de linha de comando
    :return: Nome do perfil ou None
    """
    args = sys.argv
    profile_name = None
    
    # Verifica se foi passado um argumento "-p" ou "--profile"
    for i, arg in enumerate(args):
        if arg in ("-p", "--profile") and i + 1 < len(args):
            profile_name = args[i + 1]
            write_log(f"Perfil recebido via argumento: '{profile_name}'", "Info")
            return profile_name
    
    return None

def get_profile_from_temp():
    """
    Obtém o nome do perfil do arquivo temporário
    :return: Nome do perfil ou None
    """
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                profile_name = f.read().strip()
                if profile_name:
                    write_log(f"Perfil recuperado do arquivo temporário: '{profile_name}'", "Info")
                    return profile_name
    except Exception as e:
        write_log(f"Erro ao ler perfil do arquivo temporário: {str(e)}", "Error")
    
    return None

def save_profile_to_temp(profile_name):
    """
    Salva o nome do perfil no arquivo temporário
    :param profile_name: Nome do perfil
    """
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "CloudQuest_Profile.txt")
        with open(temp_file, 'w') as f:
            f.write(profile_name)
        write_log(f"Perfil salvo no arquivo temporário: '{profile_name}'", "Info")
    except Exception as e:
        write_log(f"Erro ao salvar perfil no arquivo temporário: {str(e)}", "Error")

def load_config():
    """
    Carrega a configuração do perfil selecionado
    :return: Dicionário com a configuração
    """
    try:
        # Primeira tentativa: obter de argumentos
        profile_name = get_profile_from_args()
        
        # Segunda tentativa: obter do arquivo temporário
        if not profile_name:
            profile_name = get_profile_from_temp()
        
        # Terceira tentativa: abrir seletor de perfil
        if not profile_name:
            write_log("Nenhum perfil especificado. Abrindo seletor...", "Info")
            # Import aqui para evitar loop de importação
            from .profile_selector import select_profile
            profile_name = select_profile()
        
        if not profile_name:
            write_log("Erro: Nenhum perfil foi selecionado.", "Error")
            raise ValueError("Erro: Nome do perfil ausente.")
        
        # Salva o perfil no arquivo temporário para futuras execuções
        save_profile_to_temp(profile_name)
        
        # Constrói o caminho para o arquivo de configuração
        profiles_dir = cloud_quest_root / "profiles"
        config_path = profiles_dir / f"{profile_name}.json"
        
        write_log(f"Carregando perfil: {config_path}", "Info")
        
        if not config_path.exists():
            write_log("Arquivo de configuração do usuário não encontrado.", "Error")
            raise FileNotFoundError(f"Arquivo de configuração '{profile_name}.json' não encontrado.")
        
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
            'launcher_exe_path': user_config['ExecutablePath'],
            'profile_name': profile_name  # Adicionamos o nome do perfil ao dicionário
        }
        
        return config
    
    except Exception as e:
        write_log(f"Erro ao carregar configuração: {str(e)}", "Error")
        raise

# Inicializa o log quando o módulo é importado
init_log()