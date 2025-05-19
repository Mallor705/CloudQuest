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
            headers={'User-Agent': 'QuestConfig/1.0 (+https://github.com/Mallor705/CloudQuest)'},
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
            headers={'User-Agent': 'QuestConfig (+https://github.com/Mallor705/CloudQuest)'},
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
    
    # Extrair seção de saves - abordagem principal
    save_section = re.search(
        r'(?i)(==\s*Save game data location\s*==)(.*?)(?=\n==|\Z)',
        wikitext,
        re.DOTALL
    )
    
    if save_section:
        section_text = save_section.group(2)
        
        # Método 1: Extrair caminhos de templates de dados de jogo
        # Padrão recursivo que lida com templates aninhados, considerando chaves {} balanceadas
        windows_pattern = r'\{\{(?:Game data/(?:saves|row/PC/Save game data location)|Path/Steam game data)\|Windows\|((?:[^{}]|(?:\{\{[^{}]*\}\}))+)\}\}'
        macos_pattern = r'\{\{(?:Game data/(?:saves|row/PC/Save game data location)|Path/Steam game data)\|macOS\|((?:[^{}]|(?:\{\{[^{}]*\}\}))+)\}\}'
        linux_pattern = r'\{\{(?:Game data/(?:saves|row/PC/Save game data location)|Path/Steam game data)\|Linux\|((?:[^{}]|(?:\{\{[^{}]*\}\}))+)\}\}'
        
        # Windows
        for match in re.finditer(windows_pattern, section_text, re.DOTALL | re.IGNORECASE):
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["Windows"]:
                    results["save_locations"]["Windows"].append(path)
        
        # macOS
        for match in re.finditer(macos_pattern, section_text, re.DOTALL | re.IGNORECASE):
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["macOS"]:
                    results["save_locations"]["macOS"].append(path)
        
        # Linux
        for match in re.finditer(linux_pattern, section_text, re.DOTALL | re.IGNORECASE):
            if match:
                path = match.group(1).strip()
                if path and path not in results["save_locations"]["Linux"]:
                    results["save_locations"]["Linux"].append(path)
        
        # Método 2: Para formato alternativo {{Save game data location|...}}
        save_block = re.search(r'\{\{Save game data location(.*?)\}\}', section_text, re.DOTALL)
        if save_block:
            block_text = save_block.group(1)
            
            # Windows
            windows_match = re.search(r'\|\s*Windows\s*=\s*([^\n|]+)', block_text)
            if windows_match:
                path = windows_match.group(1).strip()
                if path and path not in results["save_locations"]["Windows"]:
                    results["save_locations"]["Windows"].append(path)
            
            # macOS
            macos_match = re.search(r'\|\s*macOS\s*=\s*([^\n|]+)', block_text)
            if macos_match:
                path = macos_match.group(1).strip()
                if path and path not in results["save_locations"]["macOS"]:
                    results["save_locations"]["macOS"].append(path)
            
            # Linux
            linux_match = re.search(r'\|\s*Linux\s*=\s*([^\n|]+)', block_text)
            if linux_match:
                path = linux_match.group(1).strip()
                if path and path not in results["save_locations"]["Linux"]:
                    results["save_locations"]["Linux"].append(path)
    
    # Método 3: Pesquisa global para formatos alternativos, como fallback
    if not any(results["save_locations"].values()):
        # Procurar por formato alternativo em qualquer lugar do documento
        save_template_patterns = [
            r'\{\{SaveFiles\|(.*?)\}\}',
            r'\{\{Save Files\|(.*?)\}\}',
            r'\{\{Save files\|(.*?)\}\}',
            r'\{\{Save game data\|(.*?)\}\}',
            r'\{\{Save Game Data\|(.*?)\}\}'
        ]
        
        for pattern in save_template_patterns:
            save_block = re.search(pattern, wikitext, re.DOTALL | re.IGNORECASE)
            if save_block:
                block_text = save_block.group(1)
                
                # Windows
                windows_match = re.search(r'\|\s*Windows\s*=\s*([^\n|]+)', block_text)
                if windows_match:
                    path = windows_match.group(1).strip()
                    if path and path not in results["save_locations"]["Windows"]:
                        results["save_locations"]["Windows"].append(path)
                
                # macOS
                macos_match = re.search(r'\|\s*macOS\s*=\s*([^\n|]+)', block_text)
                if macos_match:
                    path = macos_match.group(1).strip()
                    if path and path not in results["save_locations"]["macOS"]:
                        results["save_locations"]["macOS"].append(path)
                
                # Linux
                linux_match = re.search(r'\|\s*Linux\s*=\s*([^\n|]+)', block_text)
                if linux_match:
                    path = linux_match.group(1).strip()
                    if path and path not in results["save_locations"]["Linux"]:
                        results["save_locations"]["Linux"].append(path)
    
    # Processar templates embutidos e expandir variáveis
    for os_name in results["save_locations"]:
        processed_paths = []
        for path in results["save_locations"][os_name]:
            # Logar o caminho bruto do wikitext antes de processar
            write_log(f"Caminho bruto do wikitext ({os_name}): {path}", level='DEBUG')
            # Extrair e processar caminho completo, incluindo templates aninhados
            processed_path = process_wiki_path(path)
            
            # Limpar e normalizar o caminho
            processed_path = processed_path.strip()
            if processed_path and processed_path not in processed_paths:
                processed_paths.append(processed_path)
        
        results["save_locations"][os_name] = processed_paths
    
    write_log(f"PCGamingWiki: Encontrados {len(results['save_locations']['Windows'])} locais para Windows, "
              f"{len(results['save_locations']['macOS'])} para macOS, "
              f"{len(results['save_locations']['Linux'])} para Linux")
    
    return results

def process_wiki_path(path):
    """
    Processa um caminho do wikitext, expandindo todos os templates e variáveis.
    
    Args:
        path (str): Caminho do wikitext com possíveis templates
    
    Returns:
        str: Caminho processado
    """
    # Processar templates recursivamente
    # Este é um processo de várias etapas para lidar com templates aninhados
    
    # Substituições de templates específicos
    template_map = {
        # Templates de locais comuns do Windows
        r'\{\{p\|appdata\}\}': '%APPDATA%',
        r'\{\{p\|localappdata\}\}': '%LOCALAPPDATA%',
        r'\{\{p\|userprofile\}\}': '%USERPROFILE%',
        r'\{\{p\|documents\}\}': r'%USERPROFILE%\\Documents',
        r'\{\{p\|savedgames\}\}': r'%USERPROFILE%\\Saved Games',
        r'\{\{p\|saved games\}\}': r'%USERPROFILE%\\Saved Games',
        r'\{\{p\|programdata\}\}': '%PROGRAMDATA%',
        r'\{\{p\|commonappdata\}\}': '%PROGRAMDATA%',
        r'\{\{p\|steam\}\}': r'%PROGRAMFILES(X86)%\\Steam',
        r'\{\{p\|steamapps\}\}': r'%PROGRAMFILES(X86)%\\Steam\\steamapps',
        r'\{\{p\|steamuserdata\}\}': r'%PROGRAMFILES(X86)%\\Steam\\userdata',
        
        # Templates para variáveis específicas
        r'\{\{(?:p\|)?steamid\}\}': '<steamid>',
        r'\{\{(?:p\|)?uid\}\}': '<userid>',
        r'\{\{(?:p\|)?userid\}\}': '<userid>',
        r'\{\{(?:p\|)?username\}\}': '%USERNAME%',
        
        # Templates para diretórios macOS
        r'\{\{p\|Library/Application Support\}\}': '~/Library/Application Support',
        r'\{\{p\|Library/Containers\}\}': '~/Library/Containers',
        
        # Templates para diretórios Linux
        r'\{\{p\|\.config\}\}': '~/.config',
        r'\{\{p\|\.local/share\}\}': '~/.local/share',
        r'\{\{p\|\.steam\}\}': '~/.steam',
        r'\{\{p\|\.steam/steam/steamapps/compatdata\}\}': '~/.steam/steam/steamapps/compatdata',
        r'\{\{p\|\.local/share/Steam/steamapps/compatdata\}\}': '~/.local/share/Steam/steamapps/compatdata',

        # Novos templates para clientes
        r'\{\{p\|epicgames\}\}': r'%PROGRAMFILES%\\Epic Games',
        r'\{\{p\|gog\}\}': r'%PROGRAMFILES(X86)%\\GOG Galaxy\\Games',
        r'\{\{p\|ea\}\}': r'%PROGRAMFILES%\\EA Games',
        r'\{\{p\|ubisoft\}\}': r'%PROGRAMFILES(X86)%\\Ubisoft\\Ubisoft Game Launcher',
        
        # Caminhos do Proton
        r'\{\{p\|proton\}\}': '~/.steam/steam/steamapps/compatdata/<steamid>/pfx/drive_c',
        
        # Virtual Store
        r'\{\{p\|virtualstore\}\}': r'%LOCALAPPDATA%\\VirtualStore'
    }
    
    # Aplicar substituições específicas primeiro
    for pattern, replacement in template_map.items():
        path = re.sub(pattern, replacement, path, flags=re.IGNORECASE)
    
    # Tentar extrair conteúdo de outros templates não reconhecidos
    # Por exemplo, {{cn|Microsoft|Halo}} -> Microsoft\Halo
    cn_pattern = r'\{\{cn\|(.*?)\}\}'
    while re.search(cn_pattern, path):
        cn_match = re.search(cn_pattern, path)
        if cn_match:
            # Extrair partes do template e juntá-las com \ para Windows ou / para outros
            cn_parts = cn_match.group(1).split('|')
            if "Windows" in path:
                cn_replacement = '\\'.join(cn_parts)
            else:
                cn_replacement = '/'.join(cn_parts)
            path = path.replace(cn_match.group(0), cn_replacement)
    
    # Remover outros templates não reconhecidos
    path = re.sub(r'\{\{[^{}]*\}\}', '', path)

    # Normalizar separadores de caminho
    # Corrigido: sempre usar \ para Windows, / para outros
    if os.name == "nt":
        # Para Windows, substituir todas as barras por barra invertida
        path = path.replace('/', '\\')
        # Remover barras invertidas duplicadas
        while '\\\\' in path:
            path = path.replace('\\\\', '\\')
    else:
        # Para Unix, substituir todas as barras invertidas por barra normal
        path = path.replace('\\', '/')
        # Remover barras duplas
        while '//' in path:
            path = path.replace('//', '/')

    # Remover espaços extras e caracteres indesejados
    path = path.strip()
    path = re.sub(r'\s+', ' ', path)

    return path

def expand_windows_path(path, steam_uid=None):
    """
    Expande variáveis de ambiente do Windows em caminhos.
    
    Args:
        path (str): Caminho com variáveis de ambiente
        steam_uid (str, optional): Steam UserID do jogador

    Returns:
        str: Caminho expandido
    """
    if not path:
        return path
    
    try:
        # Substituir <USERID> pelo Steam UID fornecido
        if steam_uid:
            path = path.replace('<USERID>', steam_uid)
            path = path.replace('<userid>', steam_uid)
        else:
            path = path.replace('<USERID>', '<USERID>')
            path = path.replace('<userid>', '<userid>')
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
                "%SAVED GAMES%": str(Path.home() / "Saved Games"),
                "%PROGRAMFILES(X86)%": os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")
            }
            
            for var, replacement in env_vars.items():
                if var.lower() in expanded.lower():
                    expanded = expanded.replace(var, replacement)
                    # Também tenta a versão em lower case
                    expanded = expanded.replace(var.lower(), replacement)
        
        # Normalizar caminhos com barras duplas
        while '\\\\' in expanded:
            expanded = expanded.replace('\\\\', '\\')
        
        return expanded
    except Exception as e:
        write_log(f"Erro ao expandir caminho: {str(e)}", level='WARNING')
        return path

def expand_unix_path(path, steam_uid=None):
    """
    Expande caminhos no estilo Unix com ~ ou variáveis de ambiente.
    
    Args:
        path (str): Caminho com ~ ou variáveis
    
    Returns:
        str: Caminho expandido
    """

    # Expansão específica para caminhos do Proton
    if '<steamid>' in path:
        if not steam_uid:
            path = path.replace('<steamid>', '*')
        else:
            path = path.replace('<steamid>', steam_uid)
    
    # Converter caminhos do Proton para estrutura Linux
    proton_path = Path.home() / ".steam/steam/steamapps/compatdata"
    if str(proton_path) in path:
        path = path.replace('drive_c/users/steamuser', 'pfx/drive_c/users/steamuser')
    
    return os.path.expandvars(path)

def get_current_os_save_paths(save_locations, steam_uid=None):
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
            return [expand_windows_path(path, steam_uid) for path in paths]
    elif current_os == "Darwin":  # macOS
        paths = save_locations["macOS"]
        if paths:
            return [expand_unix_path(path, steam_uid) for path in paths]
    elif current_os == "Linux":
        paths = save_locations["Linux"]
        if paths:
            return [expand_unix_path(path, steam_uid) for path in paths]
    
    return []

def find_save_locations(steam_app_id, steam_uid=None):
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
    expanded_paths = get_current_os_save_paths(save_info["save_locations"], steam_uid)
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
                    existing_paths.append(path)
            except Exception as e:
                write_log(f"Erro ao verificar caminho {path}: {str(e)}", level='WARNING')
        
        save_info["expanded_paths"] = expanded_paths
        save_info["existing_paths"] = existing_paths
        save_info["current_os"] = current_os_name
    
    return save_info