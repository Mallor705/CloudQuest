#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para compilar o CloudQuest e QuestConfig em um único executável
usando PyInstaller.
"""

import os
import sys
import shutil
import subprocess
import glob
from pathlib import Path
import importlib

def check_dependency(module_name):
    """
    Verifica se uma dependência está instalada.
    
    Args:
        module_name: Nome do módulo a verificar
        
    Returns:
        bool: True se o módulo está instalado, False caso contrário
    """
    # PyInstaller é um caso especial - verifica via subprocess
    if module_name.lower() == 'pyinstaller':
        try:
            result = subprocess.run(['pyinstaller', '--version'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    # Para outros módulos, usa importlib
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def create_dummy_files(directory, filenames):
    """Cria arquivos dummy se não existirem."""
    os.makedirs(directory, exist_ok=True)
    
    for filename in filenames:
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            print(f"Criando arquivo dummy: {filepath}")
            with open(filepath, 'w') as f:
                f.write('# Arquivo criado automaticamente para compilacao\n')

def compile_cloudquest():
    """
    Compila o CloudQuest e QuestConfig em um único executável.
    """
    print("Iniciando compilação do CloudQuest...")
    
    # Verificar dependências
    dependencies = ["pyinstaller", "PIL", "psutil", "requests", "watchdog"]
    missing_deps = []
    
    for dep in dependencies:
        if not check_dependency(dep):
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"ERRO: Dependências necessárias não encontradas: {', '.join(missing_deps)}")
        print("Instale as dependências usando: pip install " + " ".join(missing_deps))
        return
    
    # Determinar diretórios
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    dist_dir = current_dir / "dist"
    build_dir = current_dir / "build"
    
    # Adicionar diretório atual ao PYTHONPATH para garantir importações
    sys.path.insert(0, str(current_dir))
    
    # Limpar diretórios anteriores
    if dist_dir.exists():
        print(f"Removendo diretório anterior: {dist_dir}")
        shutil.rmtree(dist_dir, ignore_errors=True)
        
    if build_dir.exists():
        print(f"Removendo diretório anterior: {build_dir}")
        shutil.rmtree(build_dir, ignore_errors=True)
    
    # Criar estrutura de diretórios necessária
    for dir_path in [
        current_dir / "assets" / "icons",
        current_dir / "logs",
        current_dir / "config" / "profiles",
        current_dir / "CloudQuest" / "config" / "profiles"
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Diretório criado/verificado: {dir_path}")
    
    # Verificar se o ícone principal existe, caso contrário criar um dummy
    app_icon = "app_icon.ico"
    icon_path = current_dir / "assets" / "icons" / app_icon
    
    if not icon_path.exists():
        print(f"AVISO: Ícone principal não encontrado em {icon_path}, criando dummy...")
        # Criar um arquivo dummy de ícone
        try:
            # Tentar criar um ícone vazio mínimo
            from PIL import Image
            img = Image.new('RGB', (32, 32), color=(73, 109, 137))
            img.save(icon_path)
            print(f"Ícone dummy criado: {icon_path}")
        except Exception as e:
            print(f"AVISO: Não foi possível criar o ícone dummy: {e}")
            # Criar um arquivo vazio como fallback
            with open(icon_path, 'wb') as f:
                f.write(b'')
    
    # Criar outros arquivos PNG dummy no diretório de ícones
    dummy_png = current_dir / "assets" / "icons" / "dummy.png"
    if not glob.glob(str(current_dir / "assets" / "icons" / "*.png")):
        try:
            from PIL import Image
            img = Image.new('RGB', (32, 32), color=(73, 109, 137))
            img.save(dummy_png)
            print(f"PNG dummy criado: {dummy_png}")
        except Exception:
            with open(dummy_png, 'wb') as f:
                f.write(b'')
    
    # Garantir que todos os __init__.py necessários existam
    required_inits = [
        current_dir / "CloudQuest" / "__init__.py",
        current_dir / "CloudQuest" / "core" / "__init__.py",
        current_dir / "CloudQuest" / "utils" / "__init__.py",
        current_dir / "CloudQuest" / "config" / "__init__.py",
        current_dir / "QuestConfig" / "__init__.py",
        current_dir / "QuestConfig" / "utils" / "__init__.py",
        current_dir / "QuestConfig" / "ui" / "__init__.py",
        current_dir / "QuestConfig" / "core" / "__init__.py",
    ]
    
    for init_file in required_inits:
        if not init_file.exists():
            init_dir = init_file.parent
            if not init_dir.exists():
                init_dir.mkdir(parents=True, exist_ok=True)
                print(f"Criando diretório: {init_dir}")
            
            with open(init_file, 'w', encoding='utf-8') as f:
                module_name = init_dir.name.capitalize()
                f.write(f'"""\nModulo {module_name} do CloudQuest.\n"""\n')
            print(f"Criado arquivo: {init_file}")
    
    # Criar arquivos de perfil dummy, se necessário
    profiles_dir = current_dir / "CloudQuest" / "config" / "profiles"
    if not any(profiles_dir.glob("*.json")):
        dummy_profile = profiles_dir / "dummy_profile.json"
        with open(dummy_profile, 'w', encoding='utf-8') as f:
            f.write('{\n  "Name": "Dummy Game",\n  "ExecutablePath": "C:/Games/Dummy/game.exe",\n  "SavePath": "C:/Users/Dummy/Saves",\n  "CloudPath": "games/dummy",\n  "GameProcess": "game.exe"\n}\n')
        print(f"Criado perfil dummy: {dummy_profile}")
    
    # Verificar os módulos reais do projeto para incluí-los
    print("Analisando módulos do projeto...")
    all_modules = []
    
    # Encontrar todos os arquivos Python em CloudQuest
    for py_file in (current_dir / "CloudQuest").glob("**/*.py"):
        if "__pycache__" not in str(py_file):
            # Converter para formato de módulo
            rel_path = py_file.relative_to(current_dir)
            module_path = str(rel_path.with_suffix('').as_posix()).replace('/', '.')
            all_modules.append(module_path)
            print(f"Módulo encontrado: {module_path}")
    
    # Encontrar todos os arquivos Python em QuestConfig
    for py_file in (current_dir / "QuestConfig").glob("**/*.py"):
        if "__pycache__" not in str(py_file):
            # Converter para formato de módulo
            rel_path = py_file.relative_to(current_dir)
            module_path = str(rel_path.with_suffix('').as_posix()).replace('/', '.')
            all_modules.append(module_path)
            print(f"Módulo encontrado: {module_path}")
    
    # Verificar e preparar recursos adicionais
    additional_resources = []
    
    # Adicionar recursos somente se existirem
    resource_paths = [
        # Os ícones NÃO devem ser incluídos no executável
        # (str(current_dir / "assets" / "icons" / "*.ico"), "assets/icons"),
        # (str(current_dir / "assets" / "icons" / "*.png"), "assets/icons"),
        # (str(current_dir / "CloudQuest" / "config" / "profiles"), "CloudQuest/config/profiles"),
        # (str(current_dir / "config" / "profiles"), "config/profiles"),
        (str(current_dir / "CloudQuest"), "CloudQuest"),
        (str(current_dir / "QuestConfig"), "QuestConfig"),
        (str(current_dir / "logs"), "logs"),
    ]
    
    for resource_path, dest in resource_paths:
        # Verificar se é um padrão glob
        if '*' in resource_path:
            if glob.glob(resource_path):
                additional_resources.append((resource_path, dest))
                print(f"Recurso adicionado: {resource_path} -> {dest}")
        elif os.path.exists(resource_path):
            additional_resources.append((resource_path, dest))
            print(f"Recurso adicionado: {resource_path} -> {dest}")
        else:
            print(f"AVISO: Recurso não encontrado: {resource_path}")
    
    # Construir comando PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--noconfirm",
        "--noupx",
        "--clean",
        "--name=CloudQuest",
        "--onefile",  # Criar um único executável
    ]
    
    # Adicionar o ícone se encontrado
    if icon_path and icon_path.exists():
        pyinstaller_args.extend([
            f"--icon={icon_path}",
            f"--add-data={icon_path};assets/icons/",
        ])
    
    # Adicionar importações ocultas obrigatórias - Módulos da biblioteca padrão
    standard_lib_modules = [
        "configparser",  # Módulo de configuração
        "io",            # Operações de I/O
        "os",            # Operações do sistema operacional
        "sys",           # Funções e variáveis do sistema
        "re",            # Expressões regulares
        "json",          # Manipulação de JSON
        "datetime",      # Manipulação de datas e horas
        "pathlib",       # Manipulação de caminhos
        "logging",       # Logging
        "subprocess",    # Execução de processos
        "time",          # Funções relacionadas ao tempo
        "shutil",        # Operações de alto nível em arquivos
        "tempfile",      # Criação de arquivos temporários
        "platform",      # Identificação da plataforma
        "glob",          # Padrões de nome de arquivo
        "socket",        # Interface de socket
        "webbrowser",    # Controle de navegador Web
        "zipfile",       # Trabalhar com arquivos ZIP
        "base64",        # Codificação/decodificação Base64
        "urllib",        # Manipulação de URLs
        "urllib.request", # Requisições HTTP
        "urllib.parse",  # Análise de URLs
        "threading",     # Threads
        "queue",         # Filas de thread
        "signal",        # Manipulação de sinais
        "uuid",          # Geração de UUIDs
        "traceback",     # Rastreamento de exceções
    ]
    
    # Adicionar importações ocultas obrigatórias - Módulos de terceiros
    third_party_modules = [
        # Importações do Tkinter
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.simpledialog",
        "tkinter.constants",
        "tkinter.font",
        "_tkinter",
        
        # Importações dos pacotes CloudQuest e QuestConfig
        "CloudQuest",
        "CloudQuest.main",
        "CloudQuest.core",
        "CloudQuest.utils",
        "CloudQuest.config",
        "QuestConfig",
        "QuestConfig.ui.app",
        
        # Bibliotecas externas
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "psutil",
        "requests",  # Biblioteca para requisições HTTP
        "watchdog",  # Biblioteca para monitoramento de arquivos
        "watchdog.events",
        "watchdog.observers",
        "win32com",
        "win32gui",
        "win32con",
        "win32api",
        "win32process",
        "win32service",
        "win32serviceutil",
        "winshell",
    ]
    
    # Combinar todos os módulos para importação
    hidden_imports = standard_lib_modules + third_party_modules
    
    # Adicionar todos os módulos do projeto como hidden imports
    hidden_imports.extend(all_modules)
    
    # Adicionar os hidden imports ao comando
    for hidden_import in hidden_imports:
        pyinstaller_args.append(f"--hidden-import={hidden_import}")
    
    # Adicionar recursos adicionais
    for resource, destination in additional_resources:
        pyinstaller_args.append(f"--add-data={resource};{destination}")
    
    # Adicionar o script principal
    pyinstaller_args.append("app.py")
    
    # Executar PyInstaller
    print("Executando PyInstaller com os seguintes argumentos:")
    print(" ".join(pyinstaller_args))
    
    try:
        subprocess.run(pyinstaller_args, check=True)
        
        # Após compilar, copiar os ícones para o diretório de distribuição
        print("\nCopiando ícones para o diretório de distribuição...")
        
        # Criar diretório de ícones ao lado do executável
        icons_dir = dist_dir / "assets" / "icons"
        icons_dir.mkdir(parents=True, exist_ok=True)
        print(f"Diretório de ícones criado: {icons_dir}")
        
        # Copiar todos os ícones PNG e ICO
        for icon_file in glob.glob(str(current_dir / "assets" / "icons" / "*.png")) + \
                          glob.glob(str(current_dir / "assets" / "icons" / "*.ico")):
            icon_path = Path(icon_file)
            dest_path = icons_dir / icon_path.name
            shutil.copy2(icon_path, dest_path)
            print(f"Ícone copiado: {icon_path.name}")
        
        print("\nCompilação concluída com sucesso!")
        print(f"Executável gerado em: {dist_dir / 'CloudQuest.exe'}")
    
    except subprocess.CalledProcessError as e:
        print(f"\nErro durante a compilação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    compile_cloudquest() 