#!/usr/bin/env python3
# CloudQuest - Gerenciador de sincronização

import os
import json
import time
from pathlib import Path

from config.settings import PROFILES_DIR
from utils.logger import log
from utils.rclone import execute_rclone_sync, test_rclone_config, create_remote_dir
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
            
        required_keys = ['RclonePath', 'CloudRemote', 'CloudDir', 'LocalDir', 'GameProcess', 'GameName']
        missing_keys = [key for key in required_keys if key not in profile]
        
        if missing_keys:
            raise ValueError(f"Chaves obrigatórias ausentes no perfil: {', '.join(missing_keys)}")
            
        # Garantir que o diretório local exista
        local_dir = Path(profile['LocalDir'])
        if not local_dir.exists():
            log.info(f"Criando diretório local: {local_dir}")
            local_dir.mkdir(parents=True, exist_ok=True)
            
        return profile
    
    except json.JSONDecodeError as e:
        log.error(f"Erro ao processar JSON do perfil: {e}")
        raise
    except Exception as e:
        log.error(f"Erro ao carregar perfil: {e}")
        raise


def sync_saves(direction, profile_name):
    """
    Sincroniza os saves do jogo.
    
    Args:
        direction (str): Direção da sincronização ('up' para local→nuvem, 'down' para nuvem→local)
        profile_name (str): Nome do perfil a ser usado
    """
    notification = None
    profile = load_profile(profile_name)
    
    try:
        # Verificar configuração do Rclone (não crítico)
        try:
            test_rclone_config(profile['RclonePath'], profile['CloudRemote'])
        except Exception as e:
            log.warning(f"Aviso: Verificação do Rclone falhou. Continuando: {e}")
        
        # Criar diretório remoto se necessário (não crítico)
        try:
            create_remote_dir(profile['RclonePath'], profile['CloudRemote'], profile['CloudDir'])
        except Exception as e:
            log.warning(f"Aviso: Falha ao criar diretório remoto. Continuando: {e}")
        
        # Determinar origem e destino com base na direção
        if direction == "down":
            # Nuvem → Local
            notification = show_notification(
                title="CloudQuest",
                message="Sincronizando",
                game_name=profile['GameName'],
                direction="sync"
            )
            source = f"{profile['CloudRemote']}:{profile['CloudDir']}/"
            destination = profile['LocalDir']
        else:
            # Local → Nuvem
            notification = show_notification(
                title="CloudQuest",
                message="Atualizando",
                game_name=profile['GameName'],
                direction="update"
            )
            source = profile['LocalDir']
            destination = f"{profile['CloudRemote']}:{profile['CloudDir']}/"
        
        # Executar sincronização
        execute_rclone_sync(profile['RclonePath'], source, destination)
        
        # Aguardar tempo mínimo de exibição da notificação
        time.sleep(5)  # 5 segundos
        
    except Exception as e:
        log.error(f"Erro na sincronização: {str(e)}")
        
        # Fechar notificação anterior se existir
        if notification:
            notification.close()
        
        # Mostrar notificação de erro
        error_notification = show_notification(
            title="Erro",
            message="Falha na sincronização",
            game_name=profile.get('GameName', 'Erro'),
            direction=direction,
            notification_type="error"
        )
        
        # Aguardar antes de fechar a notificação de erro
        time.sleep(5)
        if error_notification:
            error_notification.close()
            
        raise
    finally:
        # Garantir que a notificação seja fechada
        if notification:
            notification.close()