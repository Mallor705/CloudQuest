#!/usr/bin/env python3
# CloudQuest - Sincronizador de saves de jogos
# main.py - Ponto de entrada da aplicação

import os
import sys
import time
import argparse
import tempfile
import subprocess
from pathlib import Path
from config.settings import TEMP_PROFILE_PATH

# Determinar corretamente o diretório base da aplicação
# Isso é crucial para quando o código é convertido em executável
if getattr(sys, 'frozen', False):
    # Executando como executável empacotado (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Executando como script Python normal
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    APP_DIR = BASE_DIR

# Importações dos módulos internos
# Adicione o diretório base ao path para garantir que as importações funcionem
sys.path.insert(0, str(BASE_DIR))

from config.settings import TEMP_PROFILE_FILE
from core.sync_manager import sync_saves, load_profile
from core.game_launcher import launch_game, wait_for_game
from utils.logger import setup_logger, log

def should_launch_newgame():
    """Verifica se deve abrir o newgame (execução sem parâmetros)"""
    # Configurar o logger primeiro para garantir que podemos registrar os dados
    setup_logger(log_dir=APP_DIR / "logs")
    
    # Adicionar logs detalhados para diagnóstico
    log.debug(f"sys.argv: {sys.argv}")
    log.debug(f"is_silent_mode: {is_silent_mode()}")
    
    # CORREÇÃO: Alterado o comportamento para iniciar o newgame quando não há argumentos
    # mesmo se estiver em modo silencioso (importante para execução do EXE diretamente)
    should_launch = len(sys.argv) == 1
    log.debug(f"should_launch_newgame: {should_launch}")
    
    return should_launch

def launch_newgame():
    """Executa o newgame de acordo com o modo de execução"""
    log.info("Tentando iniciar o assistente de configuração (newgame)")
    try:
        if getattr(sys, 'frozen', False):
            # Modo executável - executar o próprio EXE com --newgame
            log.debug("Modo executável detectado, chamando o próprio EXE com --newgame")
            executable_path = sys.executable
            log.debug(f"Caminho do executável: {executable_path}")
            
            # Execute em um processo separado e não aguarde
            subprocess.Popen([executable_path, "--newgame"], 
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
            log.info("Processo do assistente iniciado com sucesso")
        else:
            # Modo script - executar normalmente
            log.debug("Modo script detectado, executando newgame.py diretamente")
            newgame_path = str(BASE_DIR / "utils" / "newgame.py")
            log.debug(f"Caminho do newgame.py: {newgame_path}")
            
            subprocess.Popen([sys.executable, newgame_path],
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0)
            log.info("Processo do assistente iniciado com sucesso")
    except Exception as e:
        log.error(f"Falha ao executar newgame: {e}", exc_info=True)
        show_error_message("Falha ao iniciar o assistente de configuração")

def main():
    """Função principal que coordena o fluxo da aplicação."""
    # Verificar se deve abrir o newgame
    if should_launch_newgame():
        # Iniciar logger antes para fazer o logging adequado
        setup_logger(log_dir=APP_DIR / "logs")
        log.info("=== Sessão iniciada ===")
        log.info("Iniciando assistente de configuração")
        
        launch_newgame()
        log.info("=== Sessão finalizada ===\n")
        sys.exit(0)
        
    # Configurar o logger se ainda não foi configurado
    setup_logger(log_dir=APP_DIR / "logs")
    log.info("=== Sessão iniciada ===")
    log.info(f"Executando a partir de: {APP_DIR}")
    log.info(f"Base dir: {BASE_DIR}")

    try:
        # 1. Obter o nome do perfil e o caminho do jogo
        profile_name, game_path = get_profile_and_path()
        if not profile_name:
            log.error("Nenhum perfil foi especificado.")
            if not is_silent_mode():
                show_error_message("Nenhum perfil foi especificado. Execute o programa com o nome do perfil como parâmetro.")
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
            sys.exit(1)

        # 2. Tentar download de saves (não crítico)
        try:
            log.info("Iniciando download de saves...")
            sync_saves(direction="down", profile_name=profile_name)
        except Exception as e:
            log.error(f"Erro no download (continuando): {str(e)}")
            # Não precisamos exibir erro ao usuário, pois isso não é crítico

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
        error_msg = f"ERRO FATAL: {str(e)}"
        log.error(error_msg, exc_info=True)
        if not is_silent_mode():
            show_error_message(error_msg)
        sys.exit(1)
    finally:
        log.info("=== Sessão finalizada ===\n")

        # Novo código para apagar o arquivo temporário
        try:
            if TEMP_PROFILE_PATH.exists():
                TEMP_PROFILE_PATH.unlink()
                log.info("Arquivo temporário do perfil removido com sucesso")
        except Exception as e:
            log.error(f"Falha ao remover arquivo temporário: {str(e)}")

def get_profile_and_path():
    """Obtém o nome do perfil e caminho do jogo."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='CloudQuest - Sincronizador de saves de jogos')
    parser.add_argument('profile', nargs='?', help='Nome do perfil a ser utilizado')
    parser.add_argument('--game-path', '-g', help='Caminho do diretório do jogo')
    parser.add_argument('--newgame', action='store_true', help=argparse.SUPPRESS)  # Parâmetro oculto
    parser.add_argument('--silent', '-s', action='store_true', help='Modo silencioso (sem diálogos)')
    
    # Suporte para uso com o Steam (através do atalho)
    # Formato: "CloudQuest.exe [PROFILE_NAME]"
    # O diretório de trabalho já é definido no campo "Iniciar em" da Steam
    try:
        args = parser.parse_args()
    except SystemExit:
        # Se falhar na análise dos argumentos (por exemplo, com --help), 
        # deixar o argparse lidar com isso normalmente
        raise

    # Se o parâmetro --newgame foi passado, abrir o assistente
    if args.newgame:
        # Usar o caminho para newgame.py dentro do executável ou no sistema de arquivos
        if getattr(sys, 'frozen', False):
            # Estamos em um executável compilado
            try:
                # Importar diretamente e executar o módulo newgame
                log.info("Importando e executando newgame.py no modo executável")
                import utils.newgame
                utils.newgame.main()
                sys.exit(0)
            except Exception as e:
                log.error(f"Erro ao importar newgame: {e}", exc_info=True)
                show_error_message(f"Erro ao iniciar o assistente: {e}")
                sys.exit(1)
        else:
            # Estamos em modo de desenvolvimento
            try:
                newgame_path = str(BASE_DIR / "utils" / "newgame.py")
                log.info(f"Executando {newgame_path} no modo desenvolvimento")
                subprocess.run([sys.executable, newgame_path], check=True)
                sys.exit(0)
            except Exception as e:
                log.error(f"Erro ao executar newgame.py: {e}", exc_info=True)
                show_error_message(f"Erro ao iniciar o assistente: {e}")
                sys.exit(1)
    
    profile_name = args.profile
    game_path = args.game_path
    
    # Se não fornecido como argumento, tentar ler do arquivo temporário
    if not profile_name:
        temp_profile_path = os.path.join(tempfile.gettempdir(), "cloudquest_profile.txt")
        if os.path.exists(temp_profile_path):
            try:
                with open(temp_profile_path, 'r') as f:
                    profile_name = f.read().strip()
                log.info(f"Perfil lido do arquivo temporário: {profile_name}")
            except Exception as e:
                log.error(f"Erro ao ler arquivo de perfil: {e}")
    
    return profile_name, game_path

def is_silent_mode():
    """Verifica se o programa está sendo executado em modo silencioso."""
    # Primeiro, verifica se a flag --silent foi passada
    if '--silent' in sys.argv or '-s' in sys.argv:
        return True
    
    # CORREÇÃO: Modificada a lógica para ser menos restritiva quando executado como EXE
    if getattr(sys, 'frozen', False):
        # Se for executado diretamente, não considerar como modo silencioso
        # se não tiver argumentos específicos, permitindo que o newgame seja iniciado
        if len(sys.argv) == 1:
            return False
        
        # Verificar apenas se tem flags específicas que indicam modo silencioso
        return any(arg in sys.argv for arg in ['--silent', '-s'])
    
    return False

def show_error_message(message):
    """Exibe uma mensagem de erro para o usuário."""
    try:
        # Em Windows, tenta usar o messagebox
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "CloudQuest - Erro", 0x10)
        else:
            # Em outros sistemas, imprime no console
            print(f"ERRO: {message}")
    except Exception:
        # Se falhar, pelo menos tenta imprimir no console
        print(f"ERRO: {message}")

if __name__ == "__main__":
    main()