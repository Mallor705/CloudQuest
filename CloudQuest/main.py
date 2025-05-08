#!/usr/bin/env python3
# CloudQuest - Sincronizador de saves de jogos
# main.py - Ponto de entrada da aplicação

import os
import sys
import time
import argparse
import tempfile
from pathlib import Path

# Importações dos módulos internos
from config.settings import TEMP_PROFILE_FILE
from core.sync_manager import sync_saves
from core.game_launcher import launch_game, wait_for_game
from utils.logger import setup_logger, log

def main():
    """Função principal que coordena o fluxo da aplicação."""
    # Configurar o logger
    setup_logger()
    log.info("=== Sessão iniciada ===")

    try:
        # 1. Obter o nome do perfil
        profile_name = get_profile_name()
        if not profile_name:
            log.error("Nenhum perfil foi especificado.")
            sys.exit(1)

        log.info(f"Perfil recebido: '{profile_name}'")

        # 2. Tentar download de saves (não crítico)
        try:
            log.info("Iniciando download de saves...")
            sync_saves(direction="down", profile_name=profile_name)
        except Exception as e:
            log.error(f"Erro no download (continuando): {str(e)}")

        # 3. Iniciar o launcher/jogo
        game_process = None
        try:
            game_process = launch_game(profile_name)
        except Exception as e:
            log.error(f"Falha ao iniciar o jogo: {str(e)}")
            sys.exit(1)

        # 4. Aguardar o término do jogo
        if game_process:
            log.info(f"Aguardando o término do processo (PID: {game_process.pid})...")
            wait_for_game(game_process)
            log.info(f"Processo finalizado (PID: {game_process.pid})")

            # 5. Tentar upload de saves (não crítico)
            try:
                log.info("Iniciando upload de saves...")
                sync_saves(direction="up", profile_name=profile_name)
            except Exception as e:
                log.error(f"Erro no upload (continuando): {str(e)}")

    except Exception as e:
        log.error(f"ERRO FATAL: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        log.info("=== Sessão finalizada ===\n")

def get_profile_name():
    """Obtém o nome do perfil do arquivo temporário ou argumentos."""
    # Verificar argumento de linha de comando
    parser = argparse.ArgumentParser(description='CloudQuest - Sincronizador de saves de jogos')
    parser.add_argument('profile', nargs='?', help='Nome do perfil a ser utilizado')
    args = parser.parse_args()
    
    # Se fornecido como argumento
    if args.profile:
        return args.profile
    
    # Tentar ler do arquivo temporário (criado pelo .bat)
    if os.path.exists(TEMP_PROFILE_FILE):
        try:
            with open(TEMP_PROFILE_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            log.error(f"Erro ao ler arquivo de perfil: {e}")
    
    return None


if __name__ == "__main__":
    main()