#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudQuest Game Configurator

Script para adicionar novos jogos à configuração do CloudQuest.
Coleta informações sobre o jogo, verifica dados na Steam, configura sincronização com Rclone
e cria perfil de configuração com atalho na área de trabalho.

Requisitos:
    Python 3.6 ou superior
    Bibliotecas: requests, unicodedata, re, json, configparser, win32com.client
"""

import os
import sys
import re
import json
import logging
import unicodedata
import configparser
import subprocess
import datetime
import requests
from pathlib import Path
import winreg
import win32com.client
import ctypes

# Configurações iniciais
script_dir = Path(__file__).resolve()
cloudquest_root = script_dir.parent
log_dir = cloudquest_root / "logs"
log_file = log_dir / "newgame.log"

# Cria o diretório de logs se não existir
log_dir.mkdir(parents=True, exist_ok=True)

# Configuração de logs
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def write_log(message, level='INFO'):
    """Escrever mensagem no arquivo de log"""
    level_map = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING, 
        'ERROR': logging.ERROR
    }
    logging.log(level_map.get(level, logging.INFO), message)

def show_header():
    """Exibe o cabeçalho do programa"""
    print("\n=== CloudQuest Game Configurator ===", flush=True)
    print(f"Versão 2.0 | {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n", flush=True)
    write_log("Início da execução do CloudQuest Game Configurator v2.0")

def validate_path(path, path_type='File'):
    """Valida se um caminho existe e é do tipo correto"""
    path_obj = Path(path)
    
    if not path_obj.exists():
        write_log(f"{path_type} não encontrado: {path}", level='WARNING')
        print(f"[AVISO] {path_type} não encontrado: {path}", flush=True)
        return False
    
    if path_type == 'File' and not path_obj.is_file():
        write_log(f"O caminho especificado não é um arquivo: {path}", level='WARNING')
        print(f"[AVISO] O caminho especificado não é um arquivo: {path}", flush=True)
        return False
    
    return True

def remove_accents(input_string):
    """Remove acentos de uma string"""
    normalized = unicodedata.normalize('NFKD', input_string)
    return ''.join([c for c in normalized if not unicodedata.combining(c)])

def input_with_default(prompt, default=None):
    """Solicita input com valor padrão"""
    if default:
        user_input = input(f"{prompt} [Enter para padrão: {default}]: ").strip()
        return default if not user_input else user_input
    else:
        return input(f"{prompt}: ").strip()

def is_admin():
    """Verifica se o script está sendo executado como administrador"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def main():
    show_header()
    
    try:
        # Passo 1: Solicitar o caminho do executável do jogo
        write_log("Iniciando etapa 1: Coleta do executável")
        while True:
            executable_path = input("Digite o caminho completo do executável do jogo (ex.: D:\\Games\\Steam\\steamapps\\common\\Jogo\\jogo.exe): ").strip('"')
            
            if not executable_path.lower().endswith('.exe'):
                write_log(f"Arquivo inválido (não é .exe): {executable_path}", level='WARNING')
                print("[AVISO] O arquivo deve ser um executável (.exe)", flush=True)
                continue
            
            if validate_path(executable_path, 'File'):
                exe_folder = Path(executable_path).parent
                write_log(f"Executável válido encontrado: {executable_path}")
                break
        
        # Passo 2: Buscar o AppID do jogo
        write_log("Iniciando etapa 2: Busca do AppID")
        steam_appid_path = exe_folder / "steam_appid.txt"
        app_id = None
        
        if validate_path(steam_appid_path, 'File'):
            try:
                with open(steam_appid_path, 'r') as f:
                    raw_content = f.read()
                
                match = re.search(r'\d{4,}', raw_content)
                if match:
                    app_id = match.group()
                    write_log(f"AppID detectado: {app_id}")
                    print(f"[+] AppID detectado: {app_id}", flush=True)
                else:
                    write_log("Arquivo steam_appid.txt sem AppID válido", level='WARNING')
                    print("[AVISO] Nenhum AppID válido encontrado no arquivo", flush=True)
                    app_id = None
            except Exception as e:
                write_log(f"Falha ao ler steam_appid.txt: {str(e)}", level='ERROR')
                print("[AVISO] Falha ao ler steam_appid.txt", flush=True)
                app_id = None
        
        if not app_id:
            write_log("Solicitando AppID manualmente")
            while True:
                app_id = input("Digite manualmente o AppID do jogo (somente números): ")
                if re.match(r'^\d+$', app_id):
                    break
            write_log(f"AppID manual inserido: {app_id}")
        
        # Passo 3: Consultar a API Steam
        write_log("Iniciando etapa 3: Consulta à API Steam")
        game_name_input = None
        api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=portuguese"
        
        try:
            print("\nConsultando API Steam...", flush=True)
            write_log(f"Consultando API Steam em: {api_url}")
            
            headers = {'User-Agent': 'CloudQuest/2.0'}
            response = requests.get(api_url, headers=headers, timeout=10)
            data = response.json()
            
            if data[app_id]['success'] and data[app_id]['data']:
                game_name_input = data[app_id]['data']['name']
                write_log(f"Nome oficial detectado: {game_name_input}")
                print(f"[+] Nome oficial detectado: {game_name_input}", flush=True)
            else:
                write_log(f"AppID {app_id} não encontrado ou dados incompletos", level='WARNING')
                print(f"[AVISO] AppID {app_id} não encontrado ou dados incompletos", flush=True)
                raise ValueError("Dados da API incompletos")
        except Exception as e:
            write_log(f"Falha na consulta à API Steam: {str(e)}", level='ERROR')
            print(f"[AVISO] Falha na consulta à API Steam: {str(e)}", flush=True)
            
            while True:
                game_name_input = input("Digite o nome do jogo: ")
                if game_name_input and not game_name_input.isspace():
                    break
            write_log(f"Nome manual inserido: {game_name_input}")
        
        # Processar o nome do jogo para usar como identificador
        game_name = remove_accents(game_name_input)
        game_name = re.sub(r'[^\w\s-]', '_', game_name)  # Remover caracteres especiais
        game_name = re.sub(r'\s+', '_', game_name)       # Substituir espaços por underline
        write_log(f"Nome oficial processado: {game_name}")
        
        # Passo 4: Configurações do Rclone
        write_log("Iniciando etapa 4: Configuração do Rclone")
        default_rclone_path = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "Rclone\\rclone.exe")
        
        while True:
            rclone_path = input_with_default("Digite o caminho do Rclone", default_rclone_path).strip('"')
            write_log(f"Verificando Rclone em: {rclone_path}")
            if validate_path(rclone_path, 'File'):
                break
        
        # Detecção automática de remotes
        rclone_conf_path = os.path.join(os.environ.get('APPDATA', ''), "rclone\\rclone.conf")
        remotes = []
        
        if validate_path(rclone_conf_path, 'File'):
            try:
                config = configparser.ConfigParser()
                config.read(rclone_conf_path)
                remotes = config.sections()
                write_log(f"Remotes detectados: {', '.join(remotes)}")
            except Exception as e:
                write_log(f"Falha ao ler rclone.conf: {str(e)}", level='ERROR')
        
        cloud_remote = None
        if remotes:
            print("\nRemotes disponíveis:", flush=True)
            for remote in remotes:
                print(f"  → {remote}", flush=True)
            
            while True:
                cloud_remote = input("Digite o nome do remote desejado: ")
                write_log(f"Tentativa de remote: {cloud_remote}")
                if cloud_remote in remotes:
                    break
        else:
            write_log("Nenhum remote configurado encontrado", level='WARNING')
            print("[AVISO] Nenhum remote configurado encontrado", flush=True)
            
            while True:
                cloud_remote = input("Digite o nome do Cloud Remote (ex.: onedrive): ")
                if cloud_remote and not cloud_remote.isspace():
                    break
            write_log(f"Remote manual inserido: {cloud_remote}")
        
        # Passo 5: Configuração de diretórios
        write_log("Iniciando etapa 5: Configuração de diretórios")
        default_local_dir = os.path.join(os.environ.get('APPDATA', ''), exe_folder.name)
        
        while True:
            local_dir_input = input_with_default("Digite o diretório local", default_local_dir).strip('"')
            local_dir = os.path.expandvars(local_dir_input)
            
            if not os.path.isabs(local_dir):
                local_dir = os.path.join(os.getcwd(), local_dir)
            
            local_dir_path = Path(local_dir)
            write_log(f"Validando diretório local: {local_dir}")
            
            if not local_dir_path.exists():
                choice = input("Diretório não existe. Criar? (S/N): ")
                if choice.lower().startswith('s'):
                    try:
                        local_dir_path.mkdir(parents=True, exist_ok=True)
                        write_log(f"Diretório criado: {local_dir}")
                        print(f"Diretório criado: {local_dir}", flush=True)
                    except Exception as e:
                        write_log(f"Falha ao criar diretório: {str(e)}", level='ERROR')
                        print(f"[AVISO] Falha ao criar diretório: {str(e)}", flush=True)
                        continue
                else:
                    write_log("Usuário optou por não criar diretório")
                    print("Por favor, insira um novo caminho", flush=True)
                    continue
            break
        
        cloud_dir_leaf = local_dir_path.name
        cloud_dir = f"CloudQuest/{cloud_dir_leaf}"
        write_log(f"Diretório cloud definido: {cloud_dir}")
        
        # Passo 6: Detecção do processo
        write_log("Iniciando etapa 6: Detecção do processo")
        game_process = Path(executable_path).stem
        print(f"\nProcesso detectado: {game_process}", flush=True)
        write_log(f"Processo detectado: {game_process}")
        
        while True:
            confirm = input("Confirmar nome do processo? (S/N): ")
            if confirm.lower().startswith('n'):
                while True:
                    game_process = input("Digite o nome correto do processo: ")
                    if game_process and not game_process.isspace():
                        break
                write_log(f"Processo manual inserido: {game_process}")
            else:
                break
        
        # Passo 7: Salvar configurações
        write_log("Iniciando etapa 7: Salvar configurações")
        config = {
            "ExecutablePath": str(executable_path),
            "ExeFolder": str(exe_folder),
            "AppID": app_id,
            "GameName": game_name_input,
            "RclonePath": rclone_path,
            "CloudRemote": cloud_remote,
            "CloudDir": cloud_dir,
            "LocalDir": str(local_dir_path),
            "GameProcess": game_process,
            "LastModified": datetime.datetime.now().isoformat()
        }
        
        config_dir = script_dir.parent / "config/profiles"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{game_name}.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        write_log(f"Configurações salvas em: {config_file}")
        print(f"\n[✓] Configurações salvas em: {config_file}", flush=True)
        
        # Passo 8: Criar atalho
        write_log("Iniciando etapa 8: Criação de atalho")
        desktop_path = Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
        shortcut_path = desktop_path / f"{game_name_input}.lnk"
        bat_path = script_dir / "cloudquest.bat"
        
        if validate_path(bat_path, 'File'):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortcut(str(shortcut_path))
                shortcut.TargetPath = 'cmd.exe'
                shortcut.Arguments = f'/c "{bat_path}" "{game_name}"'
                shortcut.WorkingDirectory = str(exe_folder)
                shortcut.IconLocation = f"{executable_path},0"
                shortcut.Save()
                
                write_log(f"Atalho criado: {shortcut_path}")
                print(f"[✓] Atalho criado: {shortcut_path}", flush=True)
            except Exception as e:
                write_log(f"Erro ao criar atalho: {str(e)}", level='ERROR')
                print(f"[AVISO] Erro ao criar atalho: {str(e)}", flush=True)
        else:
            write_log(f"Arquivo cloudquest.bat não encontrado em: {bat_path}", level='ERROR')
            print("[AVISO] Arquivo cloudquest.bat não encontrado!", flush=True)
        
        write_log("Configuração concluída com sucesso")
        print("\nConfiguração concluída com sucesso!\n", flush=True)
        
    except Exception as e:
        write_log(f"Erro fatal: {str(e)}", level='ERROR')
        print(f"\n[!] Erro durante a execução: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    # Verificar se executando com privilégios de administrador se necessário
    # if is_admin():
    main()
    # else:
    #     # Re-executa o script com privilégios de administrador se necessário
    #     print("Solicitando privilégios de administrador...")
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)