# modules/rclone.py
# VERIFICAÇÕES DO RCLONE
# ====================================================
import os
import sys
import time
import subprocess
from pathlib import Path
from .config import write_log
from .notifications import show_custom_notification

def test_rclone_config(config):
    """
    Verifica a configuração do Rclone
    :param config: Dicionário com as configurações
    """
    try:
        write_log("Verificando configuração do Rclone...", "Info")
        
        rclone_path = Path(config['rclone_path'])
        if not rclone_path.exists():
            raise FileNotFoundError(f"Arquivo do Rclone não encontrado: {rclone_path}")
        
        # Testa se o remoto está configurado
        process = subprocess.run(
            [str(rclone_path), "listremotes"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        remotes = process.stdout.strip().split('\n')
        remote_with_colon = f"{config['cloud_remote']}:"
        
        if not any(remote.startswith(remote_with_colon) for remote in remotes):
            raise ValueError(f"Remote '{config['cloud_remote']}' não configurado")
        
        write_log("Configuração do Rclone validada", "Info")
    
    except Exception as e:
        write_log(f"ERRO: Falha na verificação do Rclone - {str(e)}", "Error")
        
        # Tratamento seguro da notificação de erro
        try:
            notification = show_custom_notification(
                title="Erro de Configuração", 
                message="Verifique as configurações do Rclone", 
                type_="error"
            )
        except Exception as e2:
            write_log(f"Falha ao exibir notificação de erro do Rclone: {str(e2)}", "Error")
        
        # Repassa a exceção
        raise

def invoke_rclone_command(source, destination, notification=None):
    """
    Executa o comando Rclone com retry
    :param source: Diretório de origem
    :param destination: Diretório de destino
    :param notification: Objeto de notificação (opcional)
    """
    max_retries = 3
    retry_count = 0
    success = False
    start_time = time.time()

    try:
        while not success and retry_count < max_retries:
            try:
                write_log(f"Tentativa {retry_count+1}/{max_retries}: {source} -> {destination}", "Info")
                
                # Prepara o comando rclone
                command = [
                    Path(config['rclone_path']),
                    "copy",
                    source,
                    destination,
                    "--update",
                    "--create-empty-src-dirs"
                ]
                
                # Executa o processo com timeout
                process = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    timeout=120  # 2 minutos de timeout
                )
                
                if process.returncode != 0:
                    raise RuntimeError(f"Código de erro {process.returncode}\nSaída: {process.stdout + process.stderr}")
                
                success = True
                write_log("Sincronização bem-sucedida", "Info")
            
            except subprocess.TimeoutExpired:
                retry_count += 1
                write_log(f"Timeout na tentativa {retry_count}: O processo excedeu 2 minutos", "Warning")
                time.sleep(5)
            
            except Exception as e:
                retry_count += 1
                write_log(f"Falha na tentativa {retry_count}: {str(e)}", "Warning")
                time.sleep(5)
        
    finally:
        # Fechar notificação de forma segura
        try:
            # Fechar notificação se já passaram 5 segundos
            elapsed = time.time() - start_time
            remaining = int(5000 - (elapsed * 1000))
            
            if remaining > 0:
                time.sleep(remaining / 1000)
            
            if notification and hasattr(notification, 'close'):
                notification.close()
            process_notifications()
        except Exception as e:
            write_log(f"Erro ao fechar notificação: {str(e)}", "Warning")
    
    if not success:
        raise RuntimeError(f"Falha após {max_retries} tentativas: {source} -> {destination}")

# Variável global para armazenar a configuração
config = None

def set_config(cfg):
    """Define a configuração global para uso no módulo
    :param cfg: Dicionário de configuração
    """
    global config
    config = cfg