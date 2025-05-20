#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Gerenciador de sincronizacao.
"""

import time

from CloudQuest.core.profile_manager import load_profile
from CloudQuest.utils.logger import log
from CloudQuest.utils.rclone import execute_rclone_sync, test_rclone_config, create_remote_dir
from CloudQuest.core.notification_ui import show_notification

def sync_saves(direction, profile_name):
    """
    Sincroniza os saves do jogo.
    
    Args:
        direction (str): Direcao da sincronizacao ('up' para local→nuvem, 'down' para nuvem→local)
        profile_name (str): Nome do perfil a ser usado
    """
    notification = None
    profile = load_profile(profile_name)
    
    try:
        # Verificar configuracao do Rclone (nao critico)
        try:
            test_rclone_config(profile['RclonePath'], profile['CloudRemote'])
        except Exception as e:
            log.warning(f"Aviso: Verificacao do Rclone falhou. Continuando: {e}")
        
        # Criar diretorio remoto se necessario (nao critico)
        try:
            create_remote_dir(profile['RclonePath'], profile['CloudRemote'], profile['CloudDir'])
        except Exception as e:
            log.warning(f"Aviso: Falha ao criar diretorio remoto. Continuando: {e}")
        
        # Determinar origem e destino com base na direcao
        if direction == "down":
            # Nuvem → Local
            notification = show_notification(
                title="CloudQuest",
                message="Sincronizando",
                game_name=profile['GameName'],
                direction="down"
            )
            source = f"{profile['CloudRemote']}:{profile['CloudDir']}/"
            destination = profile['LocalDir']
        else:
            # Local → Nuvem
            notification = show_notification(
                title="CloudQuest",
                message="Atualizando",
                game_name=profile['GameName'],
                direction="up"
            )
            source = profile['LocalDir']
            destination = f"{profile['CloudRemote']}:{profile['CloudDir']}/"
        
        # Executar sincronizacao
        execute_rclone_sync(profile['RclonePath'], source, destination)
        
        # Aguardar tempo minimo de exibicao da notificacao
        time.sleep(5)  # 5 segundos
        
    except Exception as e:
        log.error(f"Erro na sincronizacao: {str(e)}")
        
        # Fechar notificacao anterior se existir
        if notification:
            notification.close()

        # Mostrar notificacao de erro
        error_notification = show_notification(
            title="Erro",
            message="Falha na sincronizacao",
            game_name=profile.get('GameName', 'Erro'),
            direction=direction,
            notification_type="error"
        )
        
        # Aguardar antes de fechar a notificacao de erro
        time.sleep(5)
        if error_notification:
            error_notification.close()
            
    finally:
        # Garantir que a notificacao seja fechada
        if notification:
            notification.close()