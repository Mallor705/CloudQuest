#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de perfis do CloudQuest.
Este modulo centraliza as operacoes relacionadas aos perfis de jogos.
"""

import json
from pathlib import Path
import platform

from CloudQuest.config.settings import PROFILES_DIR
from CloudQuest.utils.logger import log

def load_profile(profile_name):
    """
    Carrega as configuracoes do perfil do usuario.
    
    Args:
        profile_name (str): O nome do perfil a ser carregado
        
    Returns:
        dict: O perfil carregado
        
    Raises:
        FileNotFoundError: Se o arquivo de perfil nao existir
        ValueError: Se faltar dados obrigatorios no perfil
    """
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    
    if not profile_path.exists():
        log.error(f"Arquivo de configuracao nao encontrado: {profile_path}")
        raise FileNotFoundError(f"Arquivo de configuracao do usuario nao encontrado: {profile_path}")
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as file:
            profile = json.load(file)
            
        # Mapa de chaves: antigo -> novo
        key_mapping = {
            'name': 'GameName',
            'executable_path': 'ExecutablePath',
            'process_name': 'GameProcess',
            'save_location': 'LocalDir',
            'cloud_remote': 'CloudRemote',
            'cloud_dir': 'CloudDir'
        }
        
        # Lista de pares de chaves obrigatórias (formato antigo, formato novo)
        required_key_pairs = [
            ('name', 'GameName'),
            ('executable_path', 'ExecutablePath'),
            ('process_name', 'GameProcess'),
            ('save_location', 'LocalDir'),
            ('cloud_remote', 'CloudRemote'),
            ('cloud_dir', 'CloudDir')
        ]
        
        # Normaliza as chaves do perfil
        normalized_profile = {}
        
        # Primeiro copia todas as chaves existentes para o perfil normalizado
        for key, value in profile.items():
            normalized_profile[key] = value
            
            # Se esta é uma chave antiga, adiciona também com o novo nome
            if key in key_mapping:
                normalized_profile[key_mapping[key]] = value
                
        # Se não há RclonePath, adiciona um valor padrão
        if 'RclonePath' not in normalized_profile:
            if platform.system() == "Windows":
                normalized_profile['RclonePath'] = "C:\\Program Files\\rclone\\rclone.exe"
                log.info(f"RclonePath não encontrado, usando valor padrão do Windows.")
            else: # Linux, macOS, etc.
                normalized_profile['RclonePath'] = "rclone"
                log.info(f"RclonePath não encontrado, usando valor padrão 'rclone' (esperado no PATH).")
            
        # Verifica se todas as chaves obrigatórias estão presentes
        missing_keys = []
        for old_key, new_key in required_key_pairs:
            # Se nem a chave antiga nem a nova estão presentes, é um erro
            if old_key not in profile and new_key not in profile:
                missing_keys.append(f"{old_key}/{new_key}")
        
        # Adiciona RclonePath à verificação
        if 'RclonePath' not in normalized_profile:
            missing_keys.append("RclonePath")
            
        if missing_keys:
            raise ValueError(f"Chaves obrigatorias ausentes no perfil: {', '.join(missing_keys)}")
            
        # Garantir que o diretorio local exista
        local_dir_key = 'LocalDir' if 'LocalDir' in normalized_profile else 'save_location'
        local_dir = Path(normalized_profile[local_dir_key])
        if not local_dir.exists():
            log.info(f"Criando diretorio local: {local_dir}")
            local_dir.mkdir(parents=True, exist_ok=True)
            
        return normalized_profile
    
    except json.JSONDecodeError as e:
        log.error(f"Erro ao processar JSON do perfil: {e}")
        raise
    except Exception as e:
        log.error(f"Erro ao carregar perfil: {e}")
        raise
        
def list_profiles():
    """
    Lista todos os perfis disponiveis.
    
    Returns:
        list: Lista com nomes dos perfis disponiveis
    """
    profiles = []
    
    try:
        for profile_file in PROFILES_DIR.glob("*.json"):
            profiles.append(profile_file.stem)
            
        return profiles
    except Exception as e:
        log.error(f"Erro ao listar perfis: {e}")
        return []

def save_profile(profile_name, profile_data):
    """
    Salva um perfil.
    
    Args:
        profile_name (str): Nome do perfil
        profile_data (dict): Dados do perfil
        
    Returns:
        bool: True se salvo com sucesso, False caso contrario
    """
    profile_path = PROFILES_DIR / f"{profile_name}.json"
    
    try:
        with open(profile_path, 'w', encoding='utf-8') as file:
            json.dump(profile_data, file, indent=4, ensure_ascii=False)
        
        log.info(f"Perfil salvo com sucesso: {profile_name}")
        return True
    except Exception as e:
        log.error(f"Erro ao salvar perfil: {e}")
        return False 