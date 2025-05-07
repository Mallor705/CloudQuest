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
from queue import Empty

# Importando os módulos personalizados
from modules.config import load_config, write_log
from modules.rclone import test_rclone_config, invoke_rclone_command, set_config
from modules.notifications import show_custom_notification, notification_queue, _show_notification

# Variável global para configuração
config = None

def process_notifications():
    """Processa todas as notificações pendentes na fila"""
    while True:
        try:
            cmd, args = notification_queue.get_nowait()
            if cmd == 'show':
                title, message, type_, direction, game_name = args
                _show_notification(title, message, type_, direction, game_name)
            elif cmd == 'close':
                pass  # Implementação opcional para fechamento explícito
        except Empty:
            break

def find_game_process(process_name):
    """Busca o processo do jogo em toda a lista de processos"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == process_name.lower():
            return proc
    return None

def sync_saves(direction):
    """Sincroniza os saves do jogo com a nuvem"""
    notification = None
    try:
        if direction == "down":
            notification = show_custom_notification(
                title="CloudQuest",
                message="Sincronizando",
                type_="info",
                direction="down"
            )
            invoke_rclone_command(
                source=f"{config['cloud_remote']}:{config['cloud_dir']}/",
                destination=config['local_dir'],
                notification=notification
            )
            process_notifications()

        elif direction == "up":
            notification = show_custom_notification(
                title="CloudQuest",
                message="Atualizando",
                type_="info",
                direction="up"
            )
            invoke_rclone_command(
                source=config['local_dir'],
                destination=f"{config['cloud_remote']}:{config['cloud_dir']}/",
                notification=notification
            )
            process_notifications()

    except Exception as e:
        write_log(f"ERRO: Falha na sincronização - {str(e)}", "Error")
        try:
            show_custom_notification(
                title="Erro",
                message="Falha na sincronização",
                type_="error"
            )
            process_notifications()
        except Exception as e2:
            write_log(f"Erro na notificação de erro: {str(e2)}", "Error")
        raise

def main():
    global config
    root = tk.Tk()
    root.withdraw()

    try:
        # Configuração inicial
        config = load_config()
        set_config(config)

        # Verificação Rclone (não crítica)
        try:
            test_rclone_config(config)
        except Exception as e:
            write_log(f"AVISO: Verificação Rclone falhou: {str(e)}", "Warning")

        # Criação de diretórios
        try:
            subprocess.run([
                config['rclone_path'],
                "mkdir",
                f"{config['cloud_remote']}:{config['cloud_dir']}"
            ], check=True)
        except Exception as e:
            write_log(f"AVISO: Falha ao criar diretório remoto: {str(e)}", "Warning")

        local_dir = Path(config['local_dir'])
        local_dir.mkdir(parents=True, exist_ok=True)

        # Sincronização inicial
        sync_saves("down")

        # Iniciar Launcher
        launcher_path = Path(config['launcher_exe_path'])
        if not launcher_path.exists():
            raise FileNotFoundError(f"Launcher não encontrado: {launcher_path}")

        launcher_process = subprocess.Popen(
            [str(launcher_path)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        write_log(f"Launcher iniciado. PID: {launcher_process.pid}", "Info")

        # Busca pelo processo do jogo
        game_process = None
        timeout = 300  # 5 minutos
        start_time = time.time()

        while (time.time() - start_time) < timeout and not game_process:
            game_process = find_game_process(config['game_process'])
            process_notifications()
            root.update()
            time.sleep(1)

        if not game_process:
            raise RuntimeError("Processo do jogo não encontrado")

        write_log(f"Processo do jogo encontrado: {game_process.pid}", "Info")

        # Monitoramento principal
        try:
            while True:
                process_notifications()
                root.update()

                if not psutil.pid_exists(game_process.pid):
                    write_log("Processo do jogo finalizado", "Info")
                    break

                time.sleep(1)

        except Exception as e:
            write_log(f"Erro no monitoramento: {str(e)}", "Error")

        # Sincronização final
        sync_saves("up")

    except Exception as e:
        write_log(f"ERRO FATAL: {str(e)}", "Error")
        show_custom_notification(
            title="Erro Crítico",
            message="Consulte o arquivo de log",
            type_="error"
        )
        process_notifications()
        sys.exit(1)

    finally:
        try:
            root.destroy()
        except:
            pass
        write_log("=== Sessão finalizada ===\n", "Info")

if __name__ == "__main__":
    main()