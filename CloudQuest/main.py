#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Sincronizador de saves de jogos
main.py - Ponto de entrada da aplicacao
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Adicionar diretorio raiz ao path
if getattr(sys, 'frozen', False):
    # Executando como executavel empacotado (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Executando como script Python normal
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
    APP_DIR = BASE_DIR

# Adicionar diretorio base ao path para garantir que as importacoes funcionem
sys.path.insert(0, str(BASE_DIR))

# Importacoes dos modulos internos
from CloudQuest.utils.paths import APP_PATHS
from CloudQuest.config.settings import TEMP_PROFILE_PATH
from CloudQuest.core.profile_manager import load_profile
from CloudQuest.core.sync_manager import sync_saves
from CloudQuest.core.game_launcher import launch_game, wait_for_game
from CloudQuest.utils.logger import setup_logger, log

def main():
    """Funcao principal que coordena o fluxo da aplicacao."""
    
    # Configurar o parser de argumentos
    parser = argparse.ArgumentParser(description='CloudQuest - Sincronizador de saves de jogos')
    parser.add_argument('profile', nargs='?', help='Nome do perfil a ser utilizado')
    parser.add_argument('--game-path', '-g', help='Caminho do diretorio do jogo')
    parser.add_argument('--silent', '-s', action='store_true', help='Modo silencioso (sem dialogos)')
    parser.add_argument('--config', '-c', action='store_true', help='Iniciar interface de configuracao')
    
    # Suporte para uso com o Steam (atraves do atalho)
    # Formato: "CloudQuest.exe [PROFILE_NAME]"
    try:
        args = parser.parse_args()
    except SystemExit:
        # Se falhar na analise dos argumentos (por exemplo, com --help), 
        # deixar o argparse lidar com isso normalmente
        raise
    
    # Modo de configuracao: iniciar QuestConfig
    if args.config:
        run_config_interface()
        return
        
    # Configurar o logger
    setup_logger()

    log.info("=== Sessao iniciada ===")
    log.info(f"Executando a partir de: {APP_PATHS['APP_DIR']}")
    log.info(f"Base dir: {APP_PATHS['BASE_DIR']}")

    try:
        # 1. Obter o nome do perfil e o caminho do jogo
        profile_name = args.profile
        game_path = args.game_path
        
        # Se nao fornecido como argumento, tentar ler do arquivo temporario
        if not profile_name and TEMP_PROFILE_PATH.exists():
            try:
                with open(TEMP_PROFILE_PATH, 'r') as f:
                    profile_name = f.read().strip()
                log.info(f"Perfil lido do arquivo temporario: {profile_name}")
            except Exception as e:
                log.error(f"Erro ao ler arquivo de perfil: {e}")
        
        if not profile_name:
            log.info("Nenhum perfil especificado, iniciando interface de configuracao...")
            if not is_silent_mode():
                run_config_interface()
            else:
                log.error("Nenhum perfil foi especificado e modo silencioso esta ativado.")
                show_error_message("Nenhum perfil foi especificado. Execute o programa com o nome do perfil como parametro.")
            sys.exit(1)

        log.info(f"Perfil recebido: '{profile_name}'")
        if game_path:
            log.info(f"Caminho do jogo: '{game_path}'")
        
        # Verificar se o perfil existe
        try:
            profile = load_profile(profile_name)
            game_name = profile.get('GameName', 'Desconhecido')
            log.info(f"Perfil carregado com sucesso: {game_name}")
        except Exception as e:
            error_msg = f"Erro ao carregar o perfil: {str(e)}"
            log.error(error_msg)
            if not is_silent_mode():
                show_error_message(error_msg)
                # Sugerir criacao de perfil
                if show_confirm_message("Deseja criar um novo perfil?"):
                    run_config_interface()
            sys.exit(1)

        # 2. Tentar download de saves (nao critico)
        try:
            log.info("Iniciando download de saves...")
            sync_saves(direction="down", profile_name=profile_name)
        except Exception as e:
            log.error(f"Erro no download (continuando): {str(e)}")
            # Nao precisamos exibir erro ao usuario, pois isso nao e critico

        # 3. Iniciar o launcher/jogo
        game_process = None
        try:
            game_process = launch_game(profile_name)
        except Exception as e:
            error_msg = f"Falha ao iniciar o jogo: {str(e)}"
            log.error(error_msg)
            if not is_silent_mode():
                show_error_message(error_msg)
            sys.exit(1)

        # 4. Aguardar o termino do jogo
        if game_process:
            log.info(f"Aguardando o termino do processo (PID: {game_process.pid})...")
            wait_for_game(game_process)
            log.info(f"Processo finalizado (PID: {game_process.pid})")

            # 5. Tentar upload de saves (nao critico)
            try:
                log.info("Iniciando upload de saves...")
                sync_saves(direction="up", profile_name=profile_name)
            except Exception as e:
                log.error(f"Erro no upload (continuando): {str(e)}")

    except Exception as e:
        error_msg = f"ERRO FATAL: {str(e)}"
        log.error(error_msg, exc_info=True)
        if not is_silent_mode():
            show_error_message(error_msg)
        sys.exit(1)
    finally:
        log.info("=== Sessao finalizada ===\n")

        # Novo codigo para apagar o arquivo temporario
        try:
            if TEMP_PROFILE_PATH.exists():
                TEMP_PROFILE_PATH.unlink()
                log.info("Arquivo temporario do perfil removido com sucesso")
        except Exception as e:
            log.error(f"Falha ao remover arquivo temporario: {str(e)}")


def run_config_interface():
    """Inicializa e executa a interface de configuracao (QuestConfig)"""
    try:
        print("Tentando iniciar o QuestConfig...")
        # Importar o modulo QuestConfig
        sys.path.insert(0, str(BASE_DIR))
        from QuestConfig.ui.app import main as run_questconfig
        
        # Executar a interface
        print("Modulo QuestConfig importado com sucesso, iniciando interface...")
        run_questconfig()
    except ImportError as e:
        error_msg = f"Modulo de configuracao nao encontrado: {e}."
        print(error_msg)
        print("Verifique a instalacao.")
        show_error_message(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Erro ao iniciar interface de configuracao: {str(e)}"
        print(error_msg)
        show_error_message(error_msg)
        sys.exit(1)


def is_silent_mode():
    """Verifica se o programa esta sendo executado em modo silencioso."""
    # Primeiro, verifica se a flag --silent foi passada
    if '--silent' in sys.argv or '-s' in sys.argv:
        return True
    
    # CORRECAO: Modificada a logica para ser menos restritiva quando executado como EXE
    if getattr(sys, 'frozen', False):
        # Se for executado diretamente, nao considerar como modo silencioso
        if len(sys.argv) == 1:
            return False
        
        # Verificar apenas se tem flags especificas que indicam modo silencioso
        return any(arg in sys.argv for arg in ['--silent', '-s'])
    
    return False


def show_error_message(message):
    """Exibe uma mensagem de erro para o usuario."""
    print(f"EXIBINDO ERRO: {message}")
    try:
        # Em Windows, tenta usar o messagebox
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "CloudQuest - Erro", 0x10)
        else:
            # Em outros sistemas, imprime no console
            print(f"ERRO: {message}")
    except Exception as e:
        # Se falhar, pelo menos tenta imprimir no console
        print(f"ERRO ao exibir mensagem: {e}")
        print(f"ERRO: {message}")


def show_confirm_message(message):
    """Exibe uma mensagem de confirmacao para o usuario."""
    try:
        # Em Windows, tenta usar o messagebox
        if sys.platform == 'win32':
            import ctypes
            result = ctypes.windll.user32.MessageBoxW(0, message, "CloudQuest - Confirmacao", 0x24)
            return result == 6  # 6 = Sim, 7 = Nao
        else:
            # Em outros sistemas, pergunta no console
            response = input(f"{message} (S/n): ").strip().lower()
            return response == "" or response.startswith("s")
    except Exception:
        # Se falhar, assume que o usuario quer confirmar
        return True


if __name__ == "__main__":
    main()