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
import tkinter as tk
from pathlib import Path

# Importando os módulos personalizados
from modules.config import load_config, write_log
from modules.rclone import test_rclone_config, invoke_rclone_command
from modules.notifications import show_custom_notification
from modules.notifications import notification_queue

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
                    direction="sync" if direction == "down" else "up"  # Direções mapeadas
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
            process_notifications()  # Forçar atualização

        elif direction == "up":
            try:
                notification = show_custom_notification(
                    title="CloudQuest", 
                    message="Atualizando", 
                    direction="up"
                )
                if notification is None:
                    write_log("Aviso: Notificação não foi criada", "Warning")
            except Exception as e:
                write_log(f"Erro ao criar notificação: {str(e)}", "Error")

            # Continua com a sincronização mesmo se a notificação falhar
            invoke_rclone_command(
                source=config['local_dir'],
                destination=f"{config['cloud_remote']}:{config['cloud_dir']}/",
                notification=notification
            )
            process_notifications()  # Forçar atualização
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
    root = tk.Tk()  # Janela Tkinter oculta
    root.withdraw()
    
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
            
            # Após iniciar o launcher:
            write_log(f"Launcher iniciado. PID: {launcher_process.pid}, Comando: {config['launcher_exe_path']}", "Info")
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
        
        game_process_name = config['game_process']  # Define ANTES de usar
        write_log(f"Procurando por processos com nome: '{game_process_name}'", "Info")

        # Loop principal de monitoramento (código existente, mas ajustado)
        write_log("Aguardando processo do jogo...", "Info")
        timeout = 120  # Aumente o timeout aqui também
        start_time = time.time()
        game_process = None

        # Função para processar notificações na thread principal
        def process_notifications():
            while True:
                try:
                    cmd, args = notification_queue.get_nowait()
                    if cmd == 'show':
                        title, message, type_, direction, game_name = args
                        notification = _show_notification(title, message, type_, direction, game_name)
                    elif cmd == 'close':
                        if notification and hasattr(notification, 'close'):
                            notification.close()
                except queue.Empty:
                    break

        # Aguardar processo do jogo
        write_log(f"Procurando por processos com nome: '{game_process_name}'", "Info")
        timeout = 60
        start_time = time.time()
        game_process_name = config['game_process']
        # Substitua o loop de espera pelo seguinte código:
        game_process = None
        launcher_pid = launcher_process.pid

        while (time.time() - start_time) < timeout:
            try:
                launcher = psutil.Process(launcher_pid)
                # Verifica processos filhos do launcher
                children = launcher.children(recursive=True)
                for child in children:
                    if game_process_name.lower() in child.name().lower():
                        game_process = child
                        break
                if game_process:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(5)

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
                
                # Processa notificações e atualiza a interface
                process_notifications()
                root.update_idletasks()
                root.update()
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
            # Envia a notificação de erro via fila
            notification_queue.put(('show', ("Erro Crítico", "Consulte o arquivo de log", "error", "sync", None)))
        except Exception as e:
            write_log(f"Não foi possível mostrar notificação final: {str(e)}", "Error")
        sys.exit(1)
    
    finally:
        root.destroy()  # Fecha a janela Tkinter
        write_log("=== Sessão finalizada ===\n", "Info")

if __name__ == "__main__":
    # Carregar configuração
    config = load_config()
    from modules.rclone import set_config  # Adicione esta linha
    set_config(config)  # Adicione esta linha
    main()