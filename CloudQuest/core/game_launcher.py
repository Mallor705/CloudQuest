#!/usr/bin/env python3
# CloudQuest - Gerenciador de inicialização do jogo

import os
import time
import subprocess
import psutil
import json
from pathlib import Path

from config.settings import PROFILES_DIR
from utils.logger import log
from core.notification_ui import show_notification

def load_profile(profile_name):
    """Carrega as configurações do perfil do usuário."""
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    
    if not profile_path.exists():
        log.error(f"Arquivo de configuração não encontrado: {profile_path}")
        raise FileNotFoundError(f"Arquivo de configuração do usuário não encontrado: {profile_path}")
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as file:
            profile = json.load(file)
            
        required_keys = ['ExecutablePath', 'GameProcess', 'GameName']
        missing_keys = [key for key in required_keys if key not in profile]
        
        if missing_keys:
            raise ValueError(f"Chaves obrigatórias ausentes no perfil: {', '.join(missing_keys)}")
            
        return profile
    
    except json.JSONDecodeError as e:
        log.error(f"Erro ao processar JSON do perfil: {e}")
        raise
    except Exception as e:
        log.error(f"Erro ao carregar perfil: {e}")
        raise


def launch_game(profile_name):
    """
    Inicia o launcher/jogo.
    
    Args:
        profile_name (str): Nome do perfil a ser usado
        
    Returns:
        process: Objeto do processo do jogo
    """
    profile = load_profile(profile_name)
    launcher_path = profile['ExecutablePath']
    game_process_name = profile['GameProcess']
    
    # Verificar se o executável existe
    if not os.path.exists(launcher_path):
        err_msg = f"Caminho do launcher não encontrado: {launcher_path}"
        log.error(err_msg)
        
        # Mostrar notificação de erro
        error_notification = show_notification(
            title="Erro Crítico",
            message="Falha ao iniciar o jogo",
            game_name=profile.get('GameName', 'Erro'),
            notification_type="error"
        )
        time.sleep(5)
        if error_notification:
            error_notification.close()
            
        raise FileNotFoundError(err_msg)
    
    # Iniciar o launcher
    try:
        log.info(f"Iniciando launcher: {launcher_path}")
        launcher_process = subprocess.Popen(
            [launcher_path],
            # Opções para ocultar o processo
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            shell=False
        )
        
        log.info(f"Launcher iniciado (PID: {launcher_process.pid})")
        
        # Aguardar o processo do jogo iniciar
        log.info(f"Aguardando processo do jogo: {game_process_name}")
        timeout = 60  # segundos
        start_time = time.time()
        game_process = None
        
        while not game_process and (time.time() - start_time) < timeout:
            # Procurar pelo processo do jogo
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Verificar se o nome do processo corresponde, independente da extensão
                    base_name = os.path.splitext(proc.info['name'])[0].lower()
                    if base_name == game_process_name.lower():
                        game_process = proc
                        log.info(f"Processo do jogo encontrado (PID: {proc.pid})")
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
            if not game_process:
                time.sleep(1)
        
        if not game_process:
            raise TimeoutError(f"Processo do jogo não iniciado após {timeout} segundos")
            
        return game_process
        
    except Exception as e:
        log.error(f"Erro ao iniciar o launcher: {str(e)}")
        
        # Mostrar notificação de erro
        error_notification = show_notification(
            title="Erro Crítico",
            message="Falha ao iniciar o jogo",
            game_name=profile.get('GameName', 'Erro'),
            notification_type="error"
        )
        time.sleep(5)
        if error_notification:
            error_notification.close()
            
        raise


def wait_for_game(game_process):
    """
    Aguarda o jogo ser finalizado.
    
    Args:
        game_process: Objeto do processo do jogo
    """
    log.info(f"Monitorando processo do jogo (PID: {game_process.pid})...")
    
    try:
        # Verificar se o processo ainda está em execução
        while game_process.is_running() and not game_process.status() == psutil.STATUS_ZOMBIE:
            # Aguardar, verificando periodicamente
            time.sleep(0.5)
            
    except psutil.NoSuchProcess:
        log.info(f"Processo não encontrado (PID: {game_process.pid})")
    except Exception as e:
        log.error(f"Erro ao monitorar processo: {str(e)}")
        
    log.info(f"Processo finalizado (PID: {game_process.pid})")