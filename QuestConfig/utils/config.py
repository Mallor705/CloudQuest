#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gerenciador de configurações para QuestConfig.
Fornece funções para carregar e salvar configurações de jogos.
"""

import os
import json
import configparser
import datetime
from pathlib import Path

from .logger import write_log
from .path_utils import validate_path

def load_rclone_remotes():
    """
    Carrega os remotes configurados no Rclone
    
    Returns:
        list: Lista de remotes disponíveis
    """
    rclone_conf_path = os.path.join(os.environ.get('APPDATA', ''), "rclone\\rclone.conf")
    remotes = []
    
    if validate_path(rclone_conf_path, 'File'):
        try:
            config = configparser.ConfigParser()
            config.read(rclone_conf_path)
            remotes = config.sections()
            
            if remotes:
                write_log(f"Remotes detectados: {', '.join(remotes)}")
            else:
                write_log("Nenhum remote configurado encontrado", level='WARNING')
        except Exception as e:
            write_log(f"Falha ao ler rclone.conf: {str(e)}", level='ERROR')
    else:
        write_log("Arquivo rclone.conf não encontrado", level='WARNING')
    
    return remotes

def save_game_config(config_data, profiles_dir):
    """
    Salva a configuração do jogo em um arquivo JSON
    
    Args:
        config_data (dict): Dados de configuração do jogo
        profiles_dir (Path): Diretório onde salvar os perfis
    
    Returns:
        Path: Caminho do arquivo de configuração salvo ou None em caso de erro
    """
    try:
        # Garantir que o diretório existe
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Adicionar timestamp
        config_data["LastModified"] = datetime.datetime.now().isoformat()
        
        # Nome do arquivo baseado no nome interno do jogo
        internal_name = config_data.get("InternalName", "unknown_game")
        
        # Salvar arquivo de configuração
        config_file = profiles_dir / f"{internal_name}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        write_log(f"Configurações salvas em: {config_file}")
        
        # Criar diretório local se não existir
        local_dir = Path(config_data.get("LocalDir", ""))
        if local_dir and not local_dir.exists():
            local_dir.mkdir(parents=True, exist_ok=True)
            write_log(f"Diretório local criado: {local_dir}")
        
        return config_file
    
    except Exception as e:
        write_log(f"Erro ao salvar configuração: {str(e)}", level='ERROR')
        return None

def load_game_config(game_name_internal, profiles_dir):
    """
    Carrega a configuração de um jogo a partir do arquivo JSON
    
    Args:
        game_name_internal (str): Nome interno do jogo
        profiles_dir (Path): Diretório onde estão os perfis
    
    Returns:
        dict: Dados de configuração do jogo ou None se não encontrado
    """
    try:
        config_file = profiles_dir / f"{game_name_internal}.json"
        
        if not config_file.exists():
            write_log(f"Arquivo de configuração não encontrado: {config_file}", level='WARNING')
            return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        write_log(f"Configuração carregada: {game_name_internal}")
        return config_data
    
    except Exception as e:
        write_log(f"Erro ao carregar configuração: {str(e)}", level='ERROR')
        return None

def get_default_values():
    """
    Retorna valores padrão para os campos do formulário
    
    Returns:
        dict: Valores padrão
    """
    return {
        'rclone_path': os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "Rclone\\rclone.exe")
    }