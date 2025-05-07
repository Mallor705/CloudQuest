#!/usr/bin/env python
# CloudQuest.py - Script principal
# ====================================================

import os
import sys
import time
import subprocess
import threading
import tempfile
import json
import psutil
from pathlib import Path

# Importando os módulos personalizados
from modules.config import load_config, write_log
from modules.rclone import test_rclone_config, invoke_rclone_command
from modules.notifications import show_custom_notification

def sync_saves(direction):
    """
    Sincroniza os saves do jogo com a nuvem
    :param direction: "down" para baixar, "up" para subir
    """
    notification = None
    try:
        # Define mensagem e direção com base no parâmetro
        if direction == "down":
            try:
                notification = show_custom_notification(
                    title="CloudQuest", 
                    message="Sincronizando", 
                    direction="sync"
                )
                if notification is None:
                    write_log("Aviso: Notificação não foi criada", "Warning")
            except Exception as e:
                write_log(f"Erro ao criar notificação: {str(e)}", "Error")
            
            # Continua com a sincronização mesmo se a notificação falhar
            invoke_rclone_command(
                source=f"{config['cloud_remote']}:{config['cloud_dir']}/",
                destination=config['local_dir'],
                notification=notification
            )
        elif direction == "up":
            try:
                notification = show_custom_notification(
                    title="CloudQuest", 
                    message="Atualizando", 
                    direction="update"
                )
                if notification is None:
                    write_log("Aviso: Notificação não foi criada", "Warning")
            except Exception as e:
                write_log(f"Erro ao criar notificação: {str(e)}", "Error")
            
            invoke_rclone_command(
                source=config['local_dir'],
                destination=f"{config['cloud_remote']}:{config['cloud_dir']}/",
                notification=notification
            )
    except Exception as e:
        # Tratamento seguro da notificação em caso de erro
        try:
            if notification and hasattr(notification, 'close'):
                notification.close()
        except Exception as e2:
            write_log(f"Erro ao fechar notificação: {str(e2)}", "Error")
        
        write_log(f"ERRO: Falha na sincronização - {str(e)}", "Error")
        
        # Tratamento seguro da notificação de erro
        try:
            error_notification = show_custom_notification(
                title="Erro", 
                message="Falha na sincronização", 
                type_="error"
            )
            time.sleep(5)
            if error_notification and hasattr(error_notification, 'close'):
                error_notification.close()
        except Exception as e3:
            write_log(f"Falha ao exibir notificação de erro: {str(e3)}", "Error")

def main():
    global config
    
    try:
        # Verificação do Rclone (não crítico)
        try:
            test_rclone_config(config)
        except Exception as e:
            write_log(f"AVISO: Verificação do Rclone falhou. Continuando com execução... {str(e)}", "Warning")
        
        # Criar diretório remoto (não crítico)
        try:
            subprocess.run([
                config['rclone_path'], 
                "mkdir", 
                f"{config['cloud_remote']}:{config['cloud_dir']}"
            ], capture_output=True, text=True, check=True)
            write_log(f"Diretório remoto verificado/criado: {config['cloud_remote']}:{config['cloud_dir']}", "Info")
        except Exception as e:
            write_log(f"AVISO: Falha ao criar diretório remoto. Continuando... {str(e)}", "Error")

        # Criar diretório local (crítico?)
        local_dir_path = Path(config['local_dir'])
        if not local_dir_path.exists():
            try:
                local_dir_path.mkdir(parents=True, exist_ok=True)
                write_log(f"Diretório local criado: {config['local_dir']}", "Info")
            except Exception as e:
                write_log(f"ERRO: Falha ao criar diretório local. O jogo pode não funcionar corretamente. {str(e)}", "Error")
                # Não interrompe; o jogo pode criar o diretório
        
        # Download da nuvem para local
        sync_saves(direction="down")

        # Iniciar Launcher (crítico)
        launcher_process = None
        try:
            launcher_path = Path(config['launcher_exe_path'])
            if not launcher_path.exists():
                raise FileNotFoundError(f"Caminho do launcher não encontrado: {config['launcher_exe_path']}")
            
            # Inicia o processo do launcher
            launcher_process = subprocess.Popen(
                [str(launcher_path)], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if launcher_process is None or launcher_process.poll() is not None:
                raise RuntimeError("Falha ao iniciar launcher")
            
            write_log(f"Launcher iniciado (PID: {launcher_process.pid})", "Info")
        except Exception as e:
            write_log(f"ERRO FATAL: Não foi possível iniciar o launcher: {str(e)}", "Error")
            # Tentar exibir uma notificação de erro final antes de encerrar
            try:
                show_custom_notification(
                    title="Erro Crítico", 
                    message="Falha ao iniciar o jogo", 
                    type_="error"
                )
            except:
                pass
            raise  # Interrompe o script, pois sem o launcher, não há jogo
        
        # Aguardar processo do jogo
        write_log("Aguardando processo do jogo...", "Info")
        timeout = 60
        start_time = time.time()
        game_process_name = config['game_process']
        game_process = None

        while not game_process and (time.time() - start_time) < timeout:
            try:
                # Procura pelo processo do jogo
                for process in psutil.process_iter(['pid', 'name']):
                    if game_process_name.lower() in process.info['name'].lower():
                        game_process = process
                        break
            except Exception as e:
                write_log(f"Erro ao buscar o processo '{game_process_name}': {str(e)}", "Warning")
            
            if not game_process:
                time.sleep(5)

        if not game_process:
            raise TimeoutError(f"Processo do jogo não iniciado após {timeout} segundos")

        # Monitorar jogo (NÃO BLOQUEANTE)
        try:
            write_log(f"Iniciando monitoramento do processo (PID: {game_process.pid})...", "Info")
            
            # Monitoramento do processo
            while True:
                if not psutil.pid_exists(game_process.pid):
                    break
                
                # Verificação periódica
                try:
                    # Verifica se o processo ainda existe
                    process = psutil.Process(game_process.pid)
                    if not process.is_running():
                        break
                except Exception as e:
                    write_log(f"Erro ao verificar processo: {str(e)}", "Warning")
                    break
                
                time.sleep(0.5)

            write_log(f"Processo finalizado (PID: {game_process.pid})", "Info")
        except Exception as e:
            write_log(f"Erro ao monitorar o processo: {str(e)}", "Error")
            # Continuar para sincronizar mesmo se o monitoramento falhar
        
        # Upload do local para a nuvem
        sync_saves(direction="up")
    
    except Exception as e:
        write_log(f"ERRO FATAL: {str(e)}", "Error")
        import traceback
        write_log(f"Stack Trace: {traceback.format_exc()}", "Error")
        
        # Tratamento seguro da notificação final de erro
        try:
            show_custom_notification(
                title="Erro Crítico", 
                message="Consulte o arquivo de log", 
                type_="error"
            )
        except Exception as e:
            write_log(f"Não foi possível mostrar notificação final: {str(e)}", "Error")
        sys.exit(1)
    
    finally:
        write_log("=== Sessão finalizada ===\n", "Info")

if __name__ == "__main__":
    # Carregar configuração
    config = load_config()
    main()