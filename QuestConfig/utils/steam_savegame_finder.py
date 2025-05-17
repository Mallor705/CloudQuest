#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo para localização de arquivos de save de jogos via PCGamingWiki.
Oferece funções para detectar locais de save com base no AppID da Steam.
"""

import os
import re
import platform
import requests
from pathlib import Path
from .logger import write_log

def get_page_id_by_app_id(steam_app_id):
    """
    Recupera o ID da página PCGamingWiki para um jogo com base no AppID da Steam.
    
    Args:
        steam_app_id (str): AppID do jogo na Steam
    
    Returns:
        str: ID da página ou None se não encontrado
    """
    url = "https://www.pcgamingwiki.com/w/api.php"
    params = {
        "action": "cargoquery",
        "tables": "Infobox_game",
        "fields": "Infobox_game._pageID=PageID,Infobox_game.Steam_AppID",
        "where": f'Infobox_game.Steam_AppID HOLDS "{steam_app_id}"',
        "format": "json"
    }
    
    try:
        response = requests.get(
            url, 
            params=params,
            headers={'User-Agent': 'QuestConfig/1.0 (+https://github.com/questconfig)'},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        if data and "cargoquery" in data and len(data["cargoquery"]) > 0:
            write_log(f"PCGamingWiki: Encontrado PageID para AppID {steam_app_id}")
            return data["cargoquery"][0]["title"]["PageID"]
        else:
            write_log(f"PCGamingWiki: Nenhuma página encontrada para AppID {steam_app_id}", level='WARNING')
            return None
    except requests.RequestException as e:
        write_log(f"Erro ao buscar ID da página: {str(e)}", level='ERROR')
        return None

def get_wikitext_by_page_id(page_id):
    """
    Recupera o conteúdo wikitext de uma página usando seu ID.
    
    Args:
        page_id (str): ID da página PCGamingWiki
    
    Returns:
        str: Conteúdo wikitext ou None se não encontrado
    """
    url = "https://www.pcgamingwiki.com/w/api.php"
    params = {
        "action": "parse",
        "pageid": page_id,
        "prop": "wikitext",
        "format": "json"
    }
    
    try:
        response = requests.get(
            url, 
            params=params,
            headers={'User-Agent': 'QuestConfig/1.0 (+https://github.com/questconfig)'},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        if "parse" in data and "wikitext" in data["parse"] and "*" in data["parse"]["wikitext"]:
            write_log(f"PCGamingWiki: Wikitext obtido para PageID {page_id}")
            return data["parse"]["wikitext"]["*"]
        else:
            write_log(f"PCGamingWiki: Nenhum wikitext encontrado para PageID {page_id}", level='WARNING')
            return None
    except requests.RequestException as e:
        write_log(f"Erro ao buscar wikitext: {str(e)}", level='ERROR')
        return None

def extract_save_game_locations(wikitext):
    """
    Extrai locais de save do wikitext usando regex.
    
    Args:
        wikitext (str): Conteúdo wikitext da página
    
    Returns:
        dict: Informações do jogo e locais de save por OS
    """
    results = {
        "game_name": None,
        "save_locations": {
            "Windows": [],
            "macOS": [],
            "Linux": []
        }
    }
    
    # Extrair nome do jogo
    game_name_match = re.search(r"\|\s*game\s*=\s*([^\n|]+)", wikitext)
    if game_name_match:
        results["game_name"] = game_name_match.group(1).strip()
        write_log(f"PCGamingWiki: Nome do jogo encontrado: {results['game_name']}")
    
    # Extrair seção de saves
    # Procura pela seção específica de saves
    save_section = re.search(
        r'(?i)(==\s*Save game data location\s*==)(.*?)(?=\n==|\Z)',
        wikitext,
        re.DOTALL
    )
    
    if save_section:
        section_text = save_section.group(2)
        
        # Procurar por templates {{Game data/saves|Windows|...}}
        windows_templates = re.finditer(
            r'\{\{Game data/(?:saves|row/PC/Save game data location)\|Windows\|(.*?)\}\}',
            section_text,
            re.DOTALL
        )
        
        for match in windows_templates:
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["Windows"]:
                    results["save_locations"]["Windows"].append(path)
        
        # Procurar por templates para macOS
        macos_templates = re.finditer(
            r'\{\{Game data/(?:saves|row/PC/Save game data location)\|macOS\|(.*?)\}\}',
            section_text,
            re.DOTALL
        )
        
        for match in macos_templates:
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["macOS"]:
                    results["save_locations"]["macOS"].append(path)
        
        # Procurar por templates para Linux
        linux_templates = re.finditer(
            r'\{\{Game data/(?:saves|row/PC/Save game data location)\|Linux\|(.*?)\}\}',
            section_text,
            re.DOTALL
        )
        
        for match in linux_templates:
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["Linux"]:
                    results["save_locations"]["Linux"].append(path)
    
    # Se não encontrou nada, tenta buscar em outros formatos de template
    if not any(results["save_locations"].values()):
        # Procurar por formato alternativo: {{Save game data location|...}}
        save_block = re.search(r'\{\{Save game data location(.*?)\}\}', wikitext, re.DOTALL)
        if save_block:
            block_text = save_block.group(1)
            
            # Windows
            windows_match = re.search(r'\|\s*Windows\s*=\s*([^\n|]+)', block_text)
            if windows_match:
                path = windows_match.group(1).strip()
                results["save_locations"]["Windows"].append(path)
            
            # macOS
            macos_match = re.search(r'\|\s*macOS\s*=\s*([^\n|]+)', block_text)
            if macos_match:
                path = macos_match.group(1).strip()
                results["save_locations"]["macOS"].append(path)
            
            # Linux
            linux_match = re.search(r'\|\s*Linux\s*=\s*([^\n|]+)', block_text)
            if linux_match:
                path = linux_match.group(1).strip()
                results["save_locations"]["Linux"].append(path)
    
    # Processar templates embutidos e variáveis
    for os_name in results["save_locations"]:
        processed_paths = []
        for path in results["save_locations"][os_name]:
            # Corrigir templates malformados comuns
            path = re.sub(r'\{\{p\|appdata\b', '%APPDATA%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|localappdata\b', '%LOCALAPPDATA%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|userprofile\b', '%USERPROFILE%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|documents\b', r'%USERPROFILE%\\Documents', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|saved games\b', r'%USERPROFILE%\\Saved Games', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|programdata\b', '%PROGRAMDATA%', path, flags=re.IGNORECASE)

            # Substituir templates completos
            path = re.sub(r'\{\{p\|appdata\}\}', '%APPDATA%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|localappdata\}\}', '%LOCALAPPDATA%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|userprofile\}\}', '%USERPROFILE%', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|documents\}\}', r'%USERPROFILE%\\Documents', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|saved games\}\}', r'%USERPROFILE%\\Saved Games', path, flags=re.IGNORECASE)
            path = re.sub(r'\{\{p\|programdata\}\}', '%PROGRAMDATA%', path, flags=re.IGNORECASE)
            
            # Limpar outros templates restantes
            path = re.sub(r'\{\{.*?\}\}', '', path)
            
            # Limpar e normalizar o caminho
            path = path.strip()
            if path and path not in processed_paths:
                processed_paths.append(path)
        
        results["save_locations"][os_name] = processed_paths
    
    write_log(f"PCGamingWiki: Encontrados {len(results['save_locations']['Windows'])} locais para Windows, "
              f"{len(results['save_locations']['macOS'])} para macOS, "
              f"{len(results['save_locations']['Linux'])} para Linux")
    
    return results

def expand_windows_path(path):
    """
    Expande variáveis de ambiente do Windows em caminhos.
    
    Args:
        path (str): Caminho com variáveis de ambiente
    
    Returns:
        str: Caminho expandido
    """
    if not path or not '%' in path:
        return path
    
    try:
        # Usar a expansão nativa do sistema
        expanded = os.path.expandvars(path)
        
        # Se ainda contém %, tenta substituir manualmente
        if '%' in expanded:
            # Variáveis de ambiente comuns
            env_vars = {
                "%USERPROFILE%": str(Path.home()),
                "%LOCALAPPDATA%": str(Path.home() / "AppData" / "Local"),
                "%APPDATA%": str(Path.home() / "AppData" / "Roaming"),
                "%PROGRAMDATA%": os.environ.get("PROGRAMDATA", "C:/ProgramData"),
                "%DOCUMENTS%": str(Path.home() / "Documents"),
                "%SAVED GAMES%": str(Path.home() / "Saved Games")
            }
            
            for var, replacement in env_vars.items():
                if var.lower() in expanded.lower():
                    expanded = expanded.replace(var, replacement)
                    # Também tenta a versão em lower case
                    expanded = expanded.replace(var.lower(), replacement)
        
        return expanded
    except Exception as e:
        write_log(f"Erro ao expandir caminho: {str(e)}", level='WARNING')
        return path

def expand_unix_path(path):
    """
    Expande caminhos no estilo Unix com ~ ou variáveis de ambiente.
    
    Args:
        path (str): Caminho com ~ ou variáveis
    
    Returns:
        str: Caminho expandido
    """
    if not path:
        return path
    
    try:
        # Expandir ~ para home
        if '~' in path:
            path = path.replace('~', str(Path.home()))
        
        # Expandir variáveis de ambiente
        return os.path.expandvars(path)
    except Exception as e:
        write_log(f"Erro ao expandir caminho Unix: {str(e)}", level='WARNING')
        return path

def get_current_os_save_paths(save_locations):
    """
    Retorna os caminhos de save apropriados para o sistema operacional atual.
    
    Args:
        save_locations (dict): Dicionário com caminhos por OS
    
    Returns:
        list: Lista de caminhos expandidos para o OS atual
    """
    current_os = platform.system()
    
    if current_os == "Windows":
        paths = save_locations["Windows"]
        if paths:
            return [expand_windows_path(path) for path in paths]
    elif current_os == "Darwin":  # macOS
        paths = save_locations["macOS"]
        if paths:
            return [expand_unix_path(path) for path in paths]
    elif current_os == "Linux":
        paths = save_locations["Linux"]
        if paths:
            return [expand_unix_path(path) for path in paths]
    
    return []

def find_save_locations(steam_app_id):
    """
    Função principal para encontrar locais de saves para um AppID da Steam.
    
    Args:
        steam_app_id (str): AppID do jogo na Steam
    
    Returns:
        dict: Informações do jogo e locais de save ou None se não encontrado
    """
    write_log(f"Buscando locais de save para AppID Steam: {steam_app_id}")
    
    # Passo 1: Obter o ID da página
    page_id = get_page_id_by_app_id(steam_app_id)
    if not page_id:
        return None
    
    # Passo 2: Obter o wikitext
    wikitext = get_wikitext_by_page_id(page_id)
    if not wikitext:
        return None
    
    # Passo 3: Extrair locais de save
    save_info = extract_save_game_locations(wikitext)
    
    # Passo 4: Processar para o OS atual e verificar quais existem
    expanded_paths = get_current_os_save_paths(save_info["save_locations"])
    if expanded_paths:
        current_os = platform.system()
        os_mapping = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}
        current_os_name = os_mapping.get(current_os, "Unknown")
        
        # Verificar quais caminhos existem
        existing_paths = []
        for path in expanded_paths:
            try:
                if path and os.path.exists(path):
                    write_log(f"Caminho de save encontrado e existe: {path}")
                    existing_paths.append(path)
                else:
                    write_log(f"Caminho de save não existe: {path}", level='DEBUG')
            except Exception as e:
                write_log(f"Erro ao verificar caminho {path}: {str(e)}", level='WARNING')
        
        save_info["expanded_paths"] = expanded_paths
        save_info["existing_paths"] = existing_paths
        save_info["current_os"] = current_os_name
    
    return save_info
