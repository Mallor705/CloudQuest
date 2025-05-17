#!/usr/bin/env python3
# CloudQuest - Wrapper para o Rclone

import os
import subprocess
import time
from pathlib import Path

from utils.logger import log
from utils.logger import setup_logger, global_log_dir
from config.settings import RCLONE_TIMEOUT, RCLONE_MAX_RETRIES, RCLONE_RETRY_WAIT

setup_logger()

def test_rclone_config(rclone_path, cloud_remote):
    """Verifica se o Rclone está configurado corretamente."""
    log.info("Verificando configuração do Rclone...")
    
    # Verificar se o executável do Rclone existe
    if not os.path.exists(rclone_path):
        raise FileNotFoundError(f"Arquivo do Rclone não encontrado: {rclone_path}")
    
    # Listar remotes disponíveis
    try:
        result = subprocess.run(
            [rclone_path, "listremotes"],
            capture_output=True, 
            text=True, 
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,  # Adicione esta linha
            shell=False
        )
        
        remotes = result.stdout.splitlines()
        if f"{cloud_remote}:" not in remotes:
            raise ValueError(f"Remote '{cloud_remote}' não configurado")
        
        log.info("Configuração do Rclone validada")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Erro ao executar Rclone: {e}")
        log.error(f"Saída de erro: {e.stderr}")
        raise
    except Exception as e:
        log.error(f"Falha na verificação do Rclone: {str(e)}")
        raise


def create_remote_dir(rclone_path, cloud_remote, cloud_dir):
    """Cria o diretório remoto se não existir."""
    try:
        log.info(f"Verificando/criando diretório remoto: {cloud_remote}:{cloud_dir}")
        subprocess.run(
            [rclone_path, "mkdir", f"{cloud_remote}:{cloud_dir}"],
            capture_output=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,  # Adicione esta linha
            shell=False
        )
        log.info(f"Diretório remoto verificado/criado: {cloud_remote}:{cloud_dir}")
        return True
    except subprocess.CalledProcessError as e:
        log.warning(f"Falha ao criar diretório remoto: {e}")
        return False
    except Exception as e:
        log.warning(f"Erro ao criar diretório remoto: {str(e)}")
        return False


def execute_rclone_sync(rclone_path, source, destination):
    """Executa o comando Rclone para sincronização com tratamento de erros e retentativas."""
    max_retries = RCLONE_MAX_RETRIES
    retry_count = 0
    success = False
    
    log.info(f"Sincronizando: {source} -> {destination}")
    
    while not success and retry_count < max_retries:
        try:
            retry_count += 1
            log.info(f"Tentativa {retry_count}/{max_retries}")
            
            # Construir o comando
            command = [
                rclone_path,
                "copy",
                source,
                destination,
                "--progress",
                "--update",
                "--log-level=DEBUG",
                "--log-file=rclone.log",
                "--stats=5h",
                "--multi-thread-streams=8",
                "--disable-http2",
                "--ignore-checksum",
                "--create-empty-src-dirs"
            ]

            # Executar o comando
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,  # Adicione esta linha
                shell=False
                
            )
            
            # Aguardar com timeout
            try:
                stdout, stderr = process.communicate(timeout=RCLONE_TIMEOUT)
                
                if process.returncode != 0:
                    error_msg = f"Código de erro {process.returncode}\nSaída: {stderr}"
                    log.error(error_msg)
                    raise Exception(error_msg)
                
                success = True
                log.info("Sincronização bem-sucedida")
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                log.error(f"Timeout: Rclone excedeu {RCLONE_TIMEOUT} segundos.")
                
        except Exception as e:
            log.warning(f"Falha na tentativa {retry_count}: {str(e)}")
            if retry_count < max_retries:
                log.info(f"Aguardando {RCLONE_RETRY_WAIT} segundos antes da próxima tentativa...")
                time.sleep(RCLONE_RETRY_WAIT)
    
    if not success:
        raise Exception(f"Falha após {max_retries} tentativas: {source} -> {destination}")
    
    return True