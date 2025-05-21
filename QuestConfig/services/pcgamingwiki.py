# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Servico para integracao com PCGamingWiki.
Permite consultar informacoes sobre locais de saves de jogos.
"""

import re
import os
import platform
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..utils.logger import write_log
from ..interfaces.services import GameInfoService


class PCGamingWikiService(GameInfoService):
    """Servico para consultar informacoes na PCGamingWiki."""
    
    def __init__(self):
        self.base_url = "https://www.pcgamingwiki.com/w/api.php"
        self.user_agent = "QuestConfig/1.0 (+https://github.com/Mallor705/CloudQuest)"
    
    def get_game_info_by_steam_appid(self, app_id: str) -> Optional[Dict]:
        """
        Busca informacoes de um jogo pelo Steam AppID.
        
        Args:
            app_id: ID do aplicativo na Steam
            
        Returns:
            dict: Informacoes do jogo ou None se nao encontrado
        """
        try:
            write_log(f"Consultando PCGamingWiki para o AppID: {app_id}")
            
            # Primeiro, buscar o titulo pela API da Steam
            steam_info = self._query_steam_store(app_id)
            if not steam_info:
                return None
                
            game_name = steam_info.get("name", "")
            if not game_name:
                return None
            
            # Agora buscar informacoes na PCGamingWiki
            return self.get_game_info_by_name(game_name)
        except Exception as e:
            write_log(f"Erro ao consultar PCGamingWiki por AppID: {str(e)}", level='ERROR')
            return None
    
    def get_game_info_by_name(self, game_name: str) -> Optional[Dict]:
        """
        Busca informacoes de um jogo pelo nome na PCGamingWiki.
        
        Args:
            game_name: Nome do jogo
            
        Returns:
            dict: Informacoes do jogo ou None se nao encontrado
        """
        try:
            # Preparar a consulta
            params = {
                "action": "askargs",
                "format": "json",
                "conditions": f"Steam AppID::+",  # Buscar jogos com AppID definido
                "printouts": "Steam AppID|Save game data location|Save game cloud syncing|Save game cloud location",
                "parameters": f"|~*{game_name}*"  # Busca parcial pelo nome
            }
            
            # Fazer a consulta
            headers = {'User-Agent': self.user_agent}
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                write_log(f"Resposta invalida da PCGamingWiki: {response.status_code}", level='WARNING')
                return None
                
            data = response.json()
            results = data.get('query', {}).get('results', {})
            
            if not results:
                write_log(f"Nenhum resultado encontrado para: {game_name}", level='INFO')
                return None
            
            # Processar o primeiro resultado encontrado
            for page_id, info in results.items():
                game_info = {
                    "title": info.get("fulltext", ""),
                    "save_locations": self._extract_save_locations(info.get("printouts", {}))
                }
                write_log(f"Informacao encontrada na PCGamingWiki para: {game_name}")
                return game_info
            
            return None
        except Exception as e:
            write_log(f"Erro ao consultar PCGamingWiki por nome: {str(e)}", level='ERROR')
            return None
    
    def get_page_id_by_app_id(self, steam_app_id: str) -> Optional[str]:
        """
        Recupera o ID da pagina PCGamingWiki para um jogo com base no AppID da Steam.
        
        Args:
            steam_app_id: AppID do jogo na Steam
        
        Returns:
            str: ID da pagina ou None se nao encontrado
        """
        url = self.base_url
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
                headers={'User-Agent': self.user_agent},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            if data and "cargoquery" in data and len(data["cargoquery"]) > 0:
                write_log(f"PCGamingWiki: Encontrado PageID para AppID {steam_app_id}")
                return data["cargoquery"][0]["title"]["PageID"]
            else:
                write_log(f"PCGamingWiki: Nenhuma pagina encontrada para AppID {steam_app_id}", level='WARNING')
                return None
        except requests.RequestException as e:
            write_log(f"Erro ao buscar ID da pagina: {str(e)}", level='ERROR')
            return None
    
    def get_wikitext_by_page_id(self, page_id: str) -> Optional[str]:
        """
        Recupera o conteudo wikitext de uma pagina usando seu ID.
        
        Args:
            page_id: ID da pagina PCGamingWiki
        
        Returns:
            str: Conteudo wikitext ou None se nao encontrado
        """
        url = self.base_url
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
                headers={'User-Agent': self.user_agent},
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

    def extract_save_game_locations(self, wikitext: str) -> Dict:
        """
        Extrai locais de save do wikitext usando regex.
        
        Args:
            wikitext: Conteudo wikitext da pagina
        
        Returns:
            dict: Informacoes do jogo e locais de save por OS
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
        
        # Extrair secao de saves - abordagem principal
        save_section = re.search(
            r'(?i)(==\s*Save game data location\s*==)(.*?)(?=\n==|\Z)',
            wikitext,
            re.DOTALL
        )
        
        if save_section:
            section_text = save_section.group(2)
            
            # Metodo 1: Extrair caminhos de templates de dados de jogo
            # Padrao recursivo que lida com templates aninhados, considerando chaves {} balanceadas
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
            
            # Metodo 2: Para formato alternativo {{Save game data location|...}}
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
        
        # Metodo 3: Pesquisa global para formatos alternativos, como fallback
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
        
        # Processar templates embutidos e expandir variaveis
        for os_name in results["save_locations"]:
            processed_paths = []
            for path in results["save_locations"][os_name]:
                # Extrair e processar caminho completo, incluindo templates aninhados
                processed_path = self._process_wiki_path(path)
                
                # Limpar e normalizar o caminho
                processed_path = processed_path.strip()
                if processed_path and processed_path not in processed_paths:
                    processed_paths.append(processed_path)
            
            results["save_locations"][os_name] = processed_paths
        
        write_log(f"PCGamingWiki: Encontrados {len(results['save_locations']['Windows'])} locais para Windows, "
                  f"{len(results['save_locations']['macOS'])} para macOS, "
                  f"{len(results['save_locations']['Linux'])} para Linux")
        
        return results
    
    def _process_wiki_path(self, path: str) -> str:
        """
        Processa um caminho do wikitext, expandindo todos os templates e variaveis.
        
        Args:
            path: Caminho do wikitext com possiveis templates
        
        Returns:
            str: Caminho processado
        """
        # Substituicoes de templates especificos
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
            
            # Templates para variaveis especificas
            r'\{\{(?:p\|)?steamid\}\}': '<steamid>',
            r'\{\{(?:p\|)?uid\}\}': '<userid>',
            r'\{\{(?:p\|)?userid\}\}': '<userid>',
            r'\{\{(?:p\|)?username\}\}': '%USERNAME%',
            
            # Templates para diretorios macOS
            r'\{\{p\|Library/Application Support\}\}': '~/Library/Application Support',
            r'\{\{p\|Library/Containers\}\}': '~/Library/Containers',
            
            # Templates para diretorios Linux
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
        }
        
        # Aplicar substituicoes especificas primeiro
        for pattern, replacement in template_map.items():
            path = re.sub(pattern, replacement, path, flags=re.IGNORECASE)
        
        # Tentar extrair conteudo de outros templates nao reconhecidos
        # Por exemplo, {{cn|Microsoft|Halo}} -> Microsoft\Halo
        cn_pattern = r'\{\{cn\|(.*?)\}\}'
        while re.search(cn_pattern, path):
            cn_match = re.search(cn_pattern, path)
            if cn_match:
                # Extrair partes do template e junta-las com \ para Windows ou / para outros
                cn_parts = cn_match.group(1).split('|')
                if "Windows" in path:
                    cn_replacement = '\\'.join(cn_parts)
                else:
                    cn_replacement = '/'.join(cn_parts)
                path = path.replace(cn_match.group(0), cn_replacement)
        
        # Remover outros templates nao reconhecidos
        path = re.sub(r'\{\{[^{}]*\}\}', '', path)

        # Normalizar separadores de caminho
        if os.name == "nt":  # Windows
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

        # Remover espacos extras e caracteres indesejados
        path = path.strip()
        path = re.sub(r'\s+', ' ', path)

        return path

    def _find_steam_user_dir(self, base_path: str) -> Optional[str]:
        """
        Tenta encontrar automaticamente a pasta de usuario do Steam.
        
        Args:
            base_path: Caminho base onde procurar pastas de usuario
            
        Returns:
            str: Caminho completo da pasta de usuario ou None se nao encontrada
        """
        try:
            # Verificar se o diretorio base existe
            if not os.path.exists(base_path) or not os.path.isdir(base_path):
                return None
            
            write_log(f"Procurando pastas de usuario do Steam em: {base_path}")
            
            # Pastas de usuario do Steam sao numeros inteiros grandes
            user_dirs = []
            
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                
                # Verificar se e uma pasta e se o nome e numerico
                if os.path.isdir(item_path) and item.isdigit() and len(item) >= 6:
                    user_dirs.append(item_path)
            
            if not user_dirs:
                write_log("Nenhuma pasta de usuario do Steam encontrada", level='WARNING')
                return None
            
            if len(user_dirs) == 1:
                # Se so tem uma pasta, e a que queremos
                return user_dirs[0]
            else:
                # Se tem varias pastas, tentar encontrar a mais provavel
                # Criterio: pasta mais recentemente modificada e com mais conteudo
                most_recent = None
                most_recent_time = 0
                most_contents = 0
                
                for user_dir in user_dirs:
                    # Verificar data de modificacao
                    mod_time = os.path.getmtime(user_dir)
                    
                    # Contar numero de arquivos/subpastas
                    try:
                        num_contents = len(os.listdir(user_dir))
                    except:
                        num_contents = 0
                    
                    # Usar a pasta mais recente com mais conteudo
                    if mod_time > most_recent_time and num_contents > most_contents:
                        most_recent = user_dir
                        most_recent_time = mod_time
                        most_contents = num_contents
                
                if most_recent:
                    write_log(f"Varias pastas encontradas, usando a mais recente/ativa: {most_recent}")
                    return most_recent
                else:
                    # Fallback: retornar a primeira pasta encontrada
                    write_log(f"Varias pastas encontradas, usando a primeira: {user_dirs[0]}")
                    return user_dirs[0]
                
        except Exception as e:
            write_log(f"Erro ao procurar pasta de usuario: {str(e)}", level='ERROR')
            return None

    def _expand_windows_path(self, path: str, steam_uid: Optional[str] = None) -> str:
        """
        Expande variaveis de ambiente do Windows em caminhos.
        
        Args:
            path: Caminho com variaveis de ambiente
            steam_uid: Steam UserID do jogador (opcional, agora detecta automaticamente)

        Returns:
            str: Caminho expandido
        """
        if not path:
            return path
        
        try:
            # Expandir variaveis de ambiente primeiro
            expanded = os.path.expandvars(path)
            
            # Se ainda contem %, tenta substituir manualmente
            if '%' in expanded:
                # Variaveis de ambiente comuns
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
                        # Tambem tenta a versao em lower case
                        expanded = expanded.replace(var.lower(), replacement)
            
            # Detectar pastas de usuario do Steam se necessario
            if any(marker in expanded for marker in ['<USERID>', '<userid>', '<steamid>']):
                # Encontrar a parte do caminho antes do marcador de userID
                base_path = None
                for marker in ['<USERID>', '<userid>', '<steamid>']:
                    if marker in expanded:
                        # Separa o caminho em parte antes e depois do marcador
                        parts = expanded.split(marker, 1)
                        if len(parts) == 2:
                            base_path = parts[0].rstrip('\\/ ')
                            remainder = parts[1].lstrip('\\/ ')
                            
                            # Tentar encontrar a pasta do usuario automaticamente
                            user_dir = self._find_steam_user_dir(base_path)
                            if user_dir:
                                expanded = os.path.join(user_dir, remainder)
                                write_log(f"Pasta de usuario Steam detectada: {user_dir}")
                                break
            
            # Normalizar caminhos com barras duplas
            while '\\\\' in expanded:
                expanded = expanded.replace('\\\\', '\\')
            
            return expanded
            
        except Exception as e:
            write_log(f"Erro ao expandir caminho: {str(e)}", level='WARNING')
            return path

    def _expand_unix_path(self, path: str, steam_uid: Optional[str] = None, steam_app_id: Optional[str] = None) -> str:
        """
        Expande caminhos no estilo Unix com ~ ou variaveis de ambiente.
        Para Linux, transforma o caminho do Windows no formato Proton.
        
        Args:
            path: Caminho com ~ ou variaveis (originalmente para Windows)
            steam_uid: Steam UserID do jogador (opcional, agora detecta automaticamente)
            steam_app_id: Steam AppID do jogo (obrigatorio para Linux)
        
        Returns:
            str: Caminho expandido
        """
        if not path:
            return path

        try:
            # Para Linux, o 'path' recebido e o caminho do Windows.
            # Precisamos transforma-lo para o formato do Proton.
            # <SteamLibrary-folder>/steamapps/compatdata/<steam-appid>/pfx/<path listed for Windows>

            if platform.system() == "Linux":
                if not steam_app_id:
                    write_log("Steam AppID é necessário para expandir o caminho no Linux.", level='WARNING')
                    return path # Retorna o caminho original se o app_id nao for fornecido

                # Tenta encontrar a pasta da biblioteca Steam
                # Isso pode ser complexo pois podem existir varias bibliotecas
                # Por enquanto, vamos assumir uma localizacao padrao ou a primeira encontrada
                steam_library_paths = [
                    Path.home() / ".steam/steam",
                    Path.home() / ".local/share/Steam"
                ]
                
                # Adiciona caminhos de bibliotecas customizadas, se existirem
                # Esta parte pode precisar de uma logica mais robusta para encontrar todas as bibliotecas
                library_folders_vdf = Path.home() / ".steam/steam/steamapps/libraryfolders.vdf"
                if library_folders_vdf.exists():
                    try:
                        with open(library_folders_vdf, 'r') as f:
                            content = f.read()
                            # Regex para encontrar caminhos de bibliotecas adicionais
                            # Exemplo: "path" "/mnt/extra_steam_drive"
                            custom_paths = re.findall(r'\"path\"\s+\"([^\"]+)\"', content)
                            for cp in custom_paths:
                                steam_library_paths.append(Path(cp))
                    except Exception as e:
                        write_log(f"Erro ao ler libraryfolders.vdf: {e}", level='WARNING')

                proton_path_found = False
                for lib_path in steam_library_paths:
                    potential_proton_path = lib_path / "steamapps" / "compatdata" / steam_app_id / "pfx"
                    # O 'path' original e do Windows, precisamos adaptar
                    # Removendo a unidade (ex: C:) e ajustando as barras
                    current_windows_path_segment = re.sub(r'^[A-Za-z]:', '', path).replace('\\\\', '/').lstrip('/')
                    
                    # Tratar variaveis de ambiente comuns do Windows no caminho
                    # %USERPROFILE% se torna /users/steamuser/
                    # %APPDATA% se torna /users/steamuser/AppData/Roaming/
                    # %LOCALAPPDATA% se torna /users/steamuser/AppData/Local/
                    # %DOCUMENTS% se torna /users/steamuser/Documents/
                    # %SAVEDGAMES% se torna /users/steamuser/Saved Games/
                    # Outras variaveis podem precisar de tratamento especifico
                    
                    current_windows_path_segment = current_windows_path_segment.replace('%USERPROFILE%', 'users/steamuser')
                    current_windows_path_segment = current_windows_path_segment.replace('%APPDATA%', 'users/steamuser/AppData/Roaming')
                    current_windows_path_segment = current_windows_path_segment.replace('%LOCALAPPDATA%', 'users/steamuser/AppData/Local')
                    current_windows_path_segment = current_windows_path_segment.replace('%DOCUMENTS%', 'users/steamuser/Documents')
                    current_windows_path_segment = current_windows_path_segment.replace('%SAVEDGAMES%', 'users/steamuser/Saved Games')
                    current_windows_path_segment = current_windows_path_segment.replace('%PROGRAMDATA%', 'ProgramData') # Geralmente mapeado para /ProgramData

                    # --- BEGIN Steam User ID detection for Proton path ---
                    steam_id_markers = ['<steamid>', '<userid>', '<USERID>']
                    path_before_steamid_resolution = current_windows_path_segment

                    for marker in steam_id_markers:
                        if marker in path_before_steamid_resolution:
                            parts = path_before_steamid_resolution.split(marker, 1)
                            if len(parts) == 2:
                                windows_path_prefix_to_marker = parts[0]
                                windows_path_suffix_from_marker = parts[1]
                                
                                # Constroi o caminho base para _find_steam_user_dir dentro do pfx.
                                # Ex: .../compatdata/APPID/pfx/drive_c/Steam/userdata
                                # Assumimos que windows_path_prefix_to_marker contem o caminho ate a pasta userdata.
                                base_proton_userdata_path_str = str(potential_proton_path / "drive_c" / windows_path_prefix_to_marker.rstrip('/'))
                                
                                found_steam_user_dir_full_path_in_pfx = self._find_steam_user_dir(base_proton_userdata_path_str)
                                
                                if found_steam_user_dir_full_path_in_pfx:
                                    actual_user_id_folder_name = Path(found_steam_user_dir_full_path_in_pfx).name
                                    # Atualiza current_windows_path_segment com o ID resolvido
                                    current_windows_path_segment = windows_path_prefix_to_marker + actual_user_id_folder_name + windows_path_suffix_from_marker
                                    write_log(f"Steam UserID folder '{actual_user_id_folder_name}' resolvido no prefixo Proton em: {base_proton_userdata_path_str}")
                                    break # Marcador resolvido, sair do loop de marcadores
                    # --- END Steam User ID detection ---
                    
                    # Remover outros templates <...> nao explicitamente resolvidos (ex: <username>)
                    # Isso deve ser feito apos a tentativa de resolucao do steamid, para nao remover o ID numerico.
                    current_windows_path_segment = re.sub(r'<[^>]+>', '', current_windows_path_segment).strip()
                    
                    # Montar o caminho completo do Proton
                    # O pfx geralmente simula o 'drive_c'
                    full_proton_path = potential_proton_path / "drive_c" / current_windows_path_segment.lstrip('/')
                    
                    # Normalizar o caminho (remove ../, // etc)
                    normalized_path = Path(os.path.normpath(full_proton_path))
                    
                    # A PCGamingWiki as vezes fornece caminhos que ja incluem 'drive_c' ou 'users/steamuser'
                    # Vamos tentar ser flexiveis
                    if "drive_c" in path.lower():
                         # Se drive_c ja esta no path original, removemos do nosso prefixo
                        path_suffix = path.lower().split("drive_c", 1)[-1].lstrip('/').lstrip('\\\\')
                        full_proton_path = potential_proton_path / "drive_c" / path_suffix
                        normalized_path = Path(os.path.normpath(full_proton_path))

                    elif "users/steamuser" in path.lower():
                        path_suffix = path.lower().split("users/steamuser", 1)[-1].lstrip('/').lstrip('\\\\')
                        full_proton_path = potential_proton_path / "drive_c/users/steamuser" / path_suffix
                        normalized_path = Path(os.path.normpath(full_proton_path))
                        
                    # Verificar se este caminho potencial existe
                    # if normalized_path.exists(): # A existencia sera verificada depois
                    expanded = str(normalized_path)
                    proton_path_found = True
                    
                    write_log(f"Caminho Proton expandido para Linux: {expanded}")
                    break # Usa a primeira biblioteca Steam valida encontrada

                if not proton_path_found:
                    # Fallback se nenhum caminho Proton foi construido (ex: jogo nativo Linux)
                    # ou se o steam_app_id nao foi fornecido
                    expanded = os.path.expanduser(path) # Comportamento antigo para jogos nativos
                    if '<steamid>' in expanded and steam_uid: # Manter expansao de <steamid> se presente
                        expanded = expanded.replace('<steamid>', steam_uid)
                    elif '<steamid>' in expanded:
                         # Se steam_uid nao foi fornecido, tentar encontrar automaticamente
                        parts = expanded.split('<steamid>', 1)
                        if len(parts) == 2:
                            base_path_steamid = parts[0].rstrip('/ ')
                            remainder_steamid = parts[1].lstrip('/ ')
                            user_dir_steamid = self._find_steam_user_dir(base_path_steamid)
                            if user_dir_steamid:
                                expanded = os.path.join(user_dir_steamid, remainder_steamid)
                                write_log(f"Pasta de usuario Steam detectada para <steamid>: {user_dir_steamid}")
                            else:
                                write_log(f"Nao foi possivel encontrar o diretorio do usuario Steam para {base_path_steamid}", level='WARNING')
                                # Nao substitui <steamid> se nao encontrar
                    
                    # Tratar outras variaveis comuns do Linux, se houver
                    expanded = os.path.expandvars(expanded)
                    

                    write_log(f"Caminho Unix expandido (fallback/nativo): {expanded}")

            else: # Para outros sistemas Unix (ex: macOS)
                expanded = os.path.expanduser(path)
                if '<steamid>' in expanded and steam_uid:
                    expanded = expanded.replace('<steamid>', steam_uid)
                elif '<steamid>' in expanded:
                     # Se steam_uid nao foi fornecido, tentar encontrar automaticamente
                    parts = expanded.split('<steamid>', 1)
                    if len(parts) == 2:
                        base_path_steamid = parts[0].rstrip('/ ')
                        remainder_steamid = parts[1].lstrip('/ ')
                        user_dir_steamid = self._find_steam_user_dir(base_path_steamid)
                        if user_dir_steamid:
                            expanded = os.path.join(user_dir_steamid, remainder_steamid)
                            write_log(f"Pasta de usuario Steam detectada para <steamid>: {user_dir_steamid}")
                        else:
                            # Nao substitui <steamid> se nao encontrar
                            write_log(f"Nao foi possivel encontrar o diretorio do usuario Steam para {base_path_steamid}", level='WARNING')

                expanded = os.path.expandvars(expanded)
            
            # Normalizar barras duplicadas no final
            while '//' in expanded:
                expanded = expanded.replace('//', '/')
            
            return expanded
            
        except Exception as e:
            write_log(f"Erro ao expandir caminho Unix: {str(e)}\nPath original: {path}", level='ERROR')
            return path
    
    def _get_current_os_save_paths(self, save_locations: Dict, steam_uid: Optional[str] = None, steam_app_id: Optional[str] = None) -> List[str]:
        """
        Retorna os caminhos de save apropriados para o sistema operacional atual.
        
        Args:
            save_locations: Dicionario com caminhos por OS
            steam_uid: ID do usuario da Steam
            steam_app_id: ID do aplicativo Steam (necessario para Linux/Proton)
        
        Returns:
            list: Lista de caminhos expandidos para o OS atual
        """
        current_os = platform.system()
        
        if current_os == "Windows":
            paths = save_locations.get("Windows", [])
            if paths:
                return [self._expand_windows_path(path, steam_uid) for path in paths]
        
        elif current_os == "Linux":
            # Para Linux, PCGamingWiki geralmente lista o caminho do Windows.
            # Precisamos usa-lo e converter para o formato Proton.
            windows_paths = save_locations.get("Windows", [])
            linux_native_paths = save_locations.get("Linux", []) # Tambem considerar caminhos nativos
            
            expanded_linux_paths = []
            if windows_paths:
                if not steam_app_id:
                    write_log("Steam AppID nao fornecido, nao foi possivel expandir caminhos Proton para Linux.", level='WARNING')
                else:
                    for path in windows_paths:
                        expanded_linux_paths.append(self._expand_unix_path(path, steam_uid, steam_app_id))
            
            if linux_native_paths:
                 for path in linux_native_paths:
                    # Para caminhos nativos, steam_app_id nao e usado diretamente na conversao,
                    # mas pode ser necessario para resolver <steamid> se steam_uid nao for fornecido.
                    expanded_linux_paths.append(self._expand_unix_path(path, steam_uid, steam_app_id)) # Passar app_id pode ser util para _find_steam_user_dir
            
            # Remover duplicatas se houver
            return list(dict.fromkeys(expanded_linux_paths))

        elif current_os == "Darwin": # macOS
            paths = save_locations.get("macOS", [])
            if paths:
                return [self._expand_unix_path(path, steam_uid) for path in paths] # macOS nao precisa de steam_app_id para essa logica
        
        return []
    
    def find_save_locations(self, app_id: str, steam_uid: Optional[str] = None) -> Optional[Dict]:
        """
        Encontra possiveis localizacoes de saves para um jogo.
        Metodo principal - usa primeiro a API e depois o parsing do wikitext.
        
        Args:
            app_id: ID do aplicativo na Steam
            steam_uid: ID do usuario da Steam (opcional)
            
        Returns:
            dict: Dicionario com caminhos de saves ou None
        """
        write_log(f"Buscando locais de save para AppID Steam: {app_id}")
        
        # Metodo avancado com wikitext
        try:
            # Passo 1: Obter o ID da pagina
            page_id = self.get_page_id_by_app_id(app_id)
            if not page_id:
                return None
            
            # Passo 2: Obter o wikitext
            wikitext = self.get_wikitext_by_page_id(page_id)
            if not wikitext:
                return None
            
            # Passo 3: Extrair locais de save
            save_info = self.extract_save_game_locations(wikitext)
            write_log(f"Caminhos de save encontrados: {save_info}")
            # Passo 4: Processar para o OS atual e verificar quais existem
            # Passar app_id para _get_current_os_save_paths
            expanded_paths = self._get_current_os_save_paths(save_info["save_locations"], steam_uid, app_id)
            write_log(f"Caminhos expandidos: {expanded_paths}")
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
                            write_log(f"Caminho de save nao existe: {path}", level='DEBUG')
                    except Exception as e:
                        write_log(f"Erro ao verificar caminho {path}: {str(e)}", level='WARNING')
                
                result = {
                    "game_name": save_info["game_name"],
                    "original_paths": save_info["save_locations"][current_os_name],
                    "expanded_paths": expanded_paths,
                    "existing_paths": existing_paths,
                    "current_os": current_os_name
                }
                
                return result
        except Exception as e:
            write_log(f"Erro no metodo wikitext: {str(e)}", level='ERROR')
        
        return None
    
    def _query_steam_store(self, app_id: str) -> Optional[Dict]:
        """
        Consulta a API da Steam Store para obter informacoes do jogo.
        
        Args:
            app_id: ID do aplicativo na Steam
            
        Returns:
            dict: Informacoes do jogo ou None se nao encontrado
        """
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            if data.get(app_id, {}).get('success', False):
                return data[app_id]['data']
            return None
        except Exception:
            return None
    
    def _extract_save_locations(self, printouts: Dict) -> List[str]:
        """
        Extrai localizacoes de saves dos resultados da PCGamingWiki.
        
        Args:
            printouts: Resultados da consulta PCGamingWiki
            
        Returns:
            list: Lista de caminhos de saves
        """
        save_locations = []
        
        # Localizacoes locais
        if "Save game data location" in printouts:
            for item in printouts["Save game data location"]:
                if isinstance(item, dict) and "fulltext" in item:
                    path = item["fulltext"]
                    save_locations.append(path)
        
        # Localizacoes na nuvem
        if "Save game cloud location" in printouts:
            for item in printouts["Save game cloud location"]:
                if isinstance(item, dict) and "fulltext" in item:
                    path = item["fulltext"]
                    save_locations.append(path)
        
        return save_locations
    
    def _get_steam_path(self) -> str:
        """
        Tenta determinar o caminho de instalacao do Steam.
        
        Returns:
            str: Caminho do Steam ou caminho padrao
        """
        # Caminhos padrao do Steam
        default_paths = [
            # Windows
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Steam"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Steam"),
            # Linux
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam")
        ]
        
        # Verificar caminhos
        for path in default_paths:
            if os.path.exists(path) and os.path.isdir(path):
                return path
        
        # Retornar caminho mais comum se nenhum for encontrado
        return os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Steam")
    
    def detect_appid_from_file(self, executable_path: str) -> Optional[str]:
        """
        Detecta o AppID do jogo a partir de arquivos no diretorio do executavel.
        Este metodo e necessario para implementar a interface GameInfoService.
        """
        # PCGamingWiki nao implementa deteccao de AppID a partir do executavel
        return None
    
    def fetch_game_info(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta informacoes do jogo na PCGamingWiki usando o Steam AppID.
        Implementa o metodo da interface GameInfoService.
        """
        return self.get_game_info_by_steam_appid(app_id)
    
    def get_save_location(self, app_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Obtem o local de saves para um jogo.
        Implementa o metodo da interface GameInfoService.
        """
        save_info = self.find_save_locations(app_id, user_id)
        if save_info and save_info.get("existing_paths"):
            return save_info["existing_paths"][0]
        elif save_info and save_info.get("expanded_paths"):
            return save_info["expanded_paths"][0]
        return None 