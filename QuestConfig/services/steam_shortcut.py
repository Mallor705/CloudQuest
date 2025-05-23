import os
import sys
import platform
import binascii
import requests
import json
from urllib.parse import urlparse
from pathlib import Path

# Tenta importar a biblioteca vdf
try:
    import vdf
except ImportError:
    print("A biblioteca 'vdf' é necessária. Por favor, instale-a executando: pip install vdf")
    sys.exit(1)

# Para o registro do Windows, se aplicável
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        print("O módulo 'winreg' não pôde ser importado. Se você estiver no Windows, isso pode ser um problema.")

# Configuração da API do SteamGridDB
STEAMGRIDDB_API_URL = "https://www.steamgriddb.com/api/v2"
STEAMGRIDDB_API_KEY = None  # Será definida pelo usuário

def get_steamgriddb_api_key():
    """Obtém a chave da API do SteamGridDB do usuário."""
    global STEAMGRIDDB_API_KEY
    if not STEAMGRIDDB_API_KEY:
        print("\nPara baixar assets visuais automaticamente, você precisa de uma chave da API do SteamGridDB.")
        print("1. Acesse: https://www.steamgriddb.com/profile/preferences/api")
        print("2. Crie uma conta se necessário e gere uma chave da API")
        
        api_key = input("Cole sua chave da API do SteamGridDB (ou deixe em branco para pular): ").strip()
        if api_key:
            STEAMGRIDDB_API_KEY = api_key
            return True
        else:
            print("Pularemos o download automático de assets visuais.")
            return False
    return True

def search_game_steamgriddb(game_name):
    """Busca um jogo no SteamGridDB pelo nome."""
    if not STEAMGRIDDB_API_KEY:
        return None
    
    headers = {"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"}
    params = {"term": game_name}
    
    try:
        response = requests.get(f"{STEAMGRIDDB_API_URL}/search/autocomplete", 
                              headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('success') and data.get('data'):
            # Retorna o primeiro resultado
            return data['data'][0]['id']
    except Exception as e:
        print(f"Erro ao buscar jogo no SteamGridDB: {e}")
    
    return None

def get_game_assets_steamgriddb(game_id):
    """Obtém os assets de um jogo do SteamGridDB."""
    if not STEAMGRIDDB_API_KEY:
        return {}
    
    headers = {"Authorization": f"Bearer {STEAMGRIDDB_API_KEY}"}
    assets = {}
    
    # Tipos de assets disponíveis
    asset_types = {
        'grids': 'grid',      # Imagens da grid/biblioteca
        'heroes': 'hero',     # Imagens de herói (header)
        'logos': 'logo',      # Logos
        'icons': 'icon'       # Ícones
    }
    
    for endpoint, asset_type in asset_types.items():
        try:
            response = requests.get(f"{STEAMGRIDDB_API_URL}/{endpoint}/game/{game_id}",
                                  headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and data.get('data'):
                # Pega o primeiro asset de cada tipo
                assets[asset_type] = data['data'][0]['url']
        except Exception as e:
            print(f"Erro ao obter {asset_type} do SteamGridDB: {e}")
    
    return assets

def download_asset(url, filepath):
    """Baixa um asset de uma URL para um arquivo local."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Erro ao baixar asset de {url}: {e}")
        return False

def create_grid_directory(steam_path, user_id):
    """Cria o diretório grid se não existir."""
    grid_path = os.path.join(steam_path, "userdata", str(user_id), "config", "grid")
    os.makedirs(grid_path, exist_ok=True)
    return grid_path

def save_assets_to_grid(assets, app_id, grid_path):
    """Salva os assets no diretório grid com nomes apropriados."""
    saved_assets = {}
    
    # Mapeamento de tipos de asset para sufixos de arquivo
    asset_suffixes = {
        'grid': '_library_600x900.jpg',    # Imagem da biblioteca (vertical)
        'hero': '_hero.jpg',               # Imagem de herói (header)
        'logo': '_logo.png',               # Logo
        'icon': '_icon.jpg'                # Ícone
    }
    
    for asset_type, url in assets.items():
        if url:
            # Determina a extensão baseada na URL
            parsed_url = urlparse(url)
            original_ext = os.path.splitext(parsed_url.path)[1]
            
            # Usa extensão padrão se não conseguir determinar
            if asset_type == 'logo' and original_ext.lower() in ['.png', '.jpg', '.jpeg']:
                suffix = f'_logo{original_ext}'
            elif asset_type in ['grid', 'hero', 'icon'] and original_ext.lower() in ['.jpg', '.jpeg', '.png']:
                suffix = asset_suffixes[asset_type].replace('.jpg', original_ext)
            else:
                suffix = asset_suffixes.get(asset_type, f'_{asset_type}.jpg')
            
            filename = f"{app_id}{suffix}"
            filepath = os.path.join(grid_path, filename)
            
            print(f"Baixando {asset_type}: {filename}")
            if download_asset(url, filepath):
                saved_assets[asset_type] = filepath
                print(f"✓ {asset_type} salvo com sucesso")
            else:
                print(f"✗ Falha ao salvar {asset_type}")
    
    return saved_assets

def get_steam_install_path_windows():
    """Obtém o caminho de instalação da Steam do registro do Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
        winreg.CloseKey(key)
        return steam_path.replace("/", "\\")
    except FileNotFoundError:
        print("Chave do registro da Steam não encontrada.")
        return None
    except Exception as e:
        print(f"Erro ao ler o registro da Steam: {e}")
        return None

def get_steam_install_path_linux():
    """Obtém o caminho de instalação da Steam em sistemas Linux."""
    home = os.path.expanduser("~")
    common_paths = [
        os.path.join(home, ".local", "share", "Steam"),
        os.path.join(home, ".steam", "steam"),
        os.path.join(home, ".steam", "root"),
    ]
    for path in common_paths:
        if os.path.isdir(path):
            return path
    print("Diretório de instalação da Steam não encontrado no Linux.")
    return None

def get_steam_install_path_macos():
    """Obtém o caminho de instalação da Steam no macOS."""
    home = os.path.expanduser("~")
    steam_path = os.path.join(home, "Library", "Application Support", "Steam")
    if os.path.isdir(steam_path):
        return steam_path
    print("Diretório de instalação da Steam não encontrado no macOS.")
    return None

def get_steam_install_path():
    """Retorna o caminho de instalação da Steam baseado no SO."""
    os_type = platform.system()
    if os_type == "Windows":
        return get_steam_install_path_windows()
    elif os_type == "Linux":
        return get_steam_install_path_linux()
    elif os_type == "Darwin":
        return get_steam_install_path_macos()
    else:
        print(f"Sistema operacional {os_type} não suportado para detecção automática da Steam.")
        return None

def get_steam_user_ids(steam_install_path):
    """Obtém uma lista de IDs de usuário da Steam."""
    if not steam_install_path:
        return []
    userdata_path = os.path.join(steam_install_path, "userdata")
    if not os.path.isdir(userdata_path):
        print(f"Diretório userdata não encontrado em: {userdata_path}")
        return []

    user_ids = []
    for item in os.listdir(userdata_path):
        if os.path.isdir(os.path.join(userdata_path, item)):
            try:
                user_ids.append(int(item))
            except ValueError:
                pass
    if not user_ids:
        print(f"Nenhum ID de usuário da Steam encontrado em {userdata_path}")
    return user_ids

def generate_shortcut_app_id(exe_path, app_name):
    """Gera um AppID para um atalho não-Steam."""
    input_str = f"{exe_path}{app_name}"
    crc_value = binascii.crc32(input_str.encode('utf-8')) & 0xffffffff
    app_id = (crc_value | 0x80000000) & 0xffffffff
    return app_id

def create_shortcut_entry(app_name, exe_path, icon_path, app_id, start_dir):
    """Cria a estrutura de dicionário para um novo atalho."""
    return {
        'appid': app_id,
        'AppName': app_name,
        'Exe': f'"{exe_path}"',
        'StartDir': f'"{start_dir}"',
        'icon': icon_path,
        'ShortcutPath': '',
        'LaunchOptions': '',
        'IsHidden': 0,
        'AllowDesktopConfig': 1,
        'AllowOverlay': 1,
        'OpenVR': 0,
        'Devkit': 0,
        'DevkitGameID': '',
        'DevkitOverrideAppID': 0,
        'LastPlayTime': 0,
        'FlatpakAppID': '',
        'tags': {}
    }

def main():
    print("Criador de Atalhos da Steam para Jogos Não-Steam")
    print("===============================================")
    print("Com download automático de assets visuais!")
    print("")

    app_name = input("Nome do Jogo: ")
    
    while True:
        exe_path_input = input(f"Caminho completo para o executável de '{app_name}': ")
        exe_path = os.path.abspath(exe_path_input)
        if os.path.isfile(exe_path) and exe_path.lower().endswith((".exe", ".bat", ".sh", "")):
             break
        print(f"Caminho do executável inválido ou arquivo não encontrado: {exe_path_input}")
        if not input("Tentar novamente? (s/n): ").lower().startswith('s'):
            sys.exit("Criação de atalho cancelada.")

    # Pergunta sobre download de assets visuais
    download_assets = input("Deseja baixar assets visuais automaticamente? (s/n): ").lower().startswith('s')
    
    steamgriddb_game_id = None
    if download_assets:
        if get_steamgriddb_api_key():
            print(f"Buscando '{app_name}' no SteamGridDB...")
            steamgriddb_game_id = search_game_steamgriddb(app_name)
            if steamgriddb_game_id:
                print(f"✓ Jogo encontrado no SteamGridDB (ID: {steamgriddb_game_id})")
            else:
                print("✗ Jogo não encontrado no SteamGridDB")
                manual_search = input("Deseja tentar com um nome diferente? (s/n): ").lower().startswith('s')
                if manual_search:
                    alt_name = input("Digite um nome alternativo para buscar: ")
                    steamgriddb_game_id = search_game_steamgriddb(alt_name)
                    if steamgriddb_game_id:
                        print(f"✓ Jogo encontrado com nome alternativo (ID: {steamgriddb_game_id})")

    # Configuração do ícone (mantém funcionalidade original)
    icon_path_input = input(f"Caminho completo para o ícone de '{app_name}' (opcional, deixe em branco para usar o ícone do executável): ")
    icon_path = ""
    if icon_path_input.strip():
        icon_path = os.path.abspath(icon_path_input)
        if not os.path.isfile(icon_path):
            print(f"Arquivo de ícone não encontrado: {icon_path}. Usando o ícone do executável (se possível).")
            icon_path = ""
    if not icon_path:
        icon_path = exe_path

    start_dir = os.path.dirname(exe_path)

    steam_path = get_steam_install_path()
    if not steam_path:
        print("Não foi possível localizar a instalação da Steam. Saindo.")
        sys.exit(1)
    print(f"Steam encontrado em: {steam_path}")

    user_ids = get_steam_user_ids(steam_path)
    if not user_ids:
        print("Nenhum usuário da Steam encontrado para adicionar o atalho. Saindo.")
        sys.exit(1)

    app_id = generate_shortcut_app_id(exe_path, app_name)
    print(f"AppID gerado para '{app_name}': {app_id}")

    # Baixa assets se disponível
    game_assets = {}
    if steamgriddb_game_id and STEAMGRIDDB_API_KEY:
        print("Obtendo assets visuais...")
        game_assets = get_game_assets_steamgriddb(steamgriddb_game_id)
        if game_assets:
            print(f"✓ Encontrados {len(game_assets)} tipos de assets")
        else:
            print("✗ Nenhum asset encontrado")

    new_shortcut = create_shortcut_entry(app_name, exe_path, icon_path, app_id, start_dir)

    shortcuts_added_count = 0
    for user_id in user_ids:
        print(f"\nProcessando usuário Steam ID: {user_id}")
        
        # Cria diretório grid e salva assets
        if game_assets:
            grid_path = create_grid_directory(steam_path, user_id)
            print(f"Salvando assets no diretório grid: {grid_path}")
            saved_assets = save_assets_to_grid(game_assets, app_id, grid_path)
            if saved_assets:
                print(f"✓ {len(saved_assets)} assets salvos com sucesso")
        
        shortcuts_vdf_path = os.path.join(steam_path, "userdata", str(user_id), "config", "shortcuts.vdf")

        shortcuts_data = {}
        if os.path.exists(shortcuts_vdf_path):
            try:
                with open(shortcuts_vdf_path, 'rb') as f:
                    shortcuts_data = vdf.binary_load(f)
            except Exception as e:
                print(f"Erro ao ler ou analisar {shortcuts_vdf_path}: {e}")
                print("Continuando com um arquivo de atalhos vazio para este usuário.")
                shortcuts_data = {'shortcuts': {}}
        else:
            print(f"Arquivo shortcuts.vdf não encontrado em {shortcuts_vdf_path}. Um novo será criado.")
            shortcuts_data = {'shortcuts': {}}

        if not isinstance(shortcuts_data.get('shortcuts'), dict):
            print(f"Estrutura 'shortcuts' inválida no arquivo VDF para o usuário {user_id}. Corrigindo.")
            shortcuts_data['shortcuts'] = {}

        # Verifica se o atalho já existe
        shortcut_exists = False
        for _, existing_shortcut in shortcuts_data['shortcuts'].items():
            if isinstance(existing_shortcut, dict):
                if existing_shortcut.get('AppName') == app_name or \
                   existing_shortcut.get('appid') == app_id:
                    print(f"Atalho para '{app_name}' (ou mesmo AppID) já existe para o usuário {user_id}. Pulando.")
                    shortcut_exists = True
                    break
        
        if shortcut_exists:
            continue

        # Encontra o próximo índice disponível
        next_index = 0
        while str(next_index) in shortcuts_data['shortcuts']:
            next_index += 1
        
        shortcuts_data['shortcuts'][str(next_index)] = new_shortcut

        try:
            with open(shortcuts_vdf_path, 'wb') as f:
                vdf.binary_dump(shortcuts_data, f)
            print(f"✓ Atalho para '{app_name}' adicionado com sucesso para o usuário {user_id}!")
            shortcuts_added_count += 1
        except Exception as e:
            print(f"Erro ao escrever em {shortcuts_vdf_path}: {e}")
            print(f"Falha ao adicionar atalho para o usuário {user_id}.")

    print(f"\n{'='*50}")
    if shortcuts_added_count > 0:
        print(f"✓ {shortcuts_added_count} atalho(s) adicionado(s) com sucesso!")
        if game_assets:
            print("✓ Assets visuais baixados e configurados!")
        print("\n⚠️  IMPORTANTE: Reinicie a Steam para que as alterações apareçam.")
        print("   Os assets visuais podem levar alguns minutos para carregar na primeira vez.")
    else:
        print("✗ Nenhum atalho foi adicionado (possivelmente porque já existiam).")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()