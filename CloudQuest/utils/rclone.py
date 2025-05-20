#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CloudQuest - Wrapper para o Rclone.
"""

import os
import subprocess
import time

from CloudQuest.utils.logger import log, setup_logger
from CloudQuest.config.settings import RCLONE_TIMEOUT, RCLONE_MAX_RETRIES, RCLONE_RETRY_WAIT

# Garantir que o logger esteja configurado
setup_logger()

def test_rclone_config(rclone_path, cloud_remote):
    """
    Verifica se o Rclone esta configurado corretamente.
    
    Args:
        rclone_path (str): Caminho para o executavel do Rclone
        cloud_remote (str): Nome do remote a ser verificado
        
    Returns:
        bool: True se a configuracao esta correta
        
    Raises:
        FileNotFoundError: Se o Rclone nao for encontrado
        ValueError: Se o remote nao estiver configurado
    """
    log.info("Verificando configuracao do Rclone...")
    
    # Verificar se o executavel do Rclone existe
    if not os.path.exists(rclone_path):
        raise FileNotFoundError(f"Arquivo do Rclone nao encontrado: {rclone_path}")
    
    # Listar remotes disponiveis
    try:
        result = subprocess.run(
            [rclone_path, "listremotes"],
            capture_output=True, 
            text=True, 
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            shell=False
        )
        
        remotes = result.stdout.splitlines()
        if f"{cloud_remote}:" not in remotes:
            raise ValueError(f"Remote '{cloud_remote}' nao configurado")
        
        log.info("Configuracao do Rclone validada")
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Erro ao executar Rclone: {e}")
        log.error(f"Saida de erro: {e.stderr}")
        raise
    except Exception as e:
        log.error(f"Falha na verificacao do Rclone: {str(e)}")
        raise


def create_remote_dir(rclone_path, cloud_remote, cloud_dir):
    """
    Cria o diretorio remoto se nao existir.
    
    Args:
        rclone_path (str): Caminho para o executavel do Rclone
        cloud_remote (str): Nome do remote
        cloud_dir (str): Diretorio remoto
        
    Returns:
        bool: True se criado ou ja existente
    """
    try:
        log.info(f"Verificando/criando diretorio remoto: {cloud_remote}:{cloud_dir}")
        subprocess.run(
            [rclone_path, "mkdir", f"{cloud_remote}:{cloud_dir}"],
            capture_output=True,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            shell=False
        )
        log.info(f"Diretorio remoto verificado/criado: {cloud_remote}:{cloud_dir}")
        return True
    except subprocess.CalledProcessError as e:
        log.warning(f"Falha ao criar diretorio remoto: {e}")
        return False
    except Exception as e:
        log.warning(f"Erro ao criar diretorio remoto: {str(e)}")
        return False


def execute_rclone_sync(rclone_path, source, destination):
    """
    Executa o comando Rclone para sincronizacao com tratamento de erros e retentativas.
    
    Args:
        rclone_path (str): Caminho para o executavel do Rclone
        source (str): Origem da sincronizacao
        destination (str): Destino da sincronizacao
        
    Returns:
        bool: True se bem sucedido
        
    Raises:
        Exception: Se todas as tentativas falharem
    """
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
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                shell=False
            )
            
            # Aguardar com timeout
            try:
                stdout, stderr = process.communicate(timeout=RCLONE_TIMEOUT)
                
                if process.returncode != 0:
                    error_msg = f"Codigo de erro {process.returncode}\nSaida: {stderr}"
                    log.error(error_msg)
                    raise Exception(error_msg)
                
                success = True
                log.info("Sincronizacao bem-sucedida")
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                log.error(f"Timeout: Rclone excedeu {RCLONE_TIMEOUT} segundos.")
                
        except Exception as e:
            log.warning(f"Falha na tentativa {retry_count}: {str(e)}")
            if retry_count < max_retries:
                log.info(f"Aguardando {RCLONE_RETRY_WAIT} segundos antes da proxima tentativa...")
                time.sleep(RCLONE_RETRY_WAIT)
    
    if not success:
        raise Exception(f"Falha apos {max_retries} tentativas: {source} -> {destination}")
    
    return True