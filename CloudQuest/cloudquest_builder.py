#!/usr/bin/env python3
# CloudQuest - Script para criar o executável usando PyInstaller

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """
    Cria o executável do CloudQuest usando PyInstaller.
    """
    print("=== CloudQuest - Gerador de Executável ===")
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"PyInstaller encontrado: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Verificar outras dependências
    dependencies = ["psutil", "Pillow"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"{dep} já instalado")
        except ImportError:
            print(f"{dep} não encontrado. Instalando...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep])
    
    # Diretório atual
    current_dir = Path.cwd()
    
    # Nome do arquivo de saída
    output_name = "CloudQuest"
    
    # Criar diretório temporário para build
    build_dir = current_dir / "build_tmp"
    build_dir.mkdir(exist_ok=True)
    
    # Arquivos e pastas para copiar para o diretório de build
    files_to_copy = [
        "main.py",
        "config",
        "core",
        "utils",
        "assets"
    ]
    
    # Copiar arquivos para o diretório de build
    for file in files_to_copy:
        src_path = current_dir / file
        dst_path = build_dir / file
        
        if src_path.is_dir():
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(src_path, dst_path)
            print(f"Diretório copiado: {file}")
        elif src_path.is_file():
            shutil.copy2(src_path, dst_path)
            print(f"Arquivo copiado: {file}")
        else:
            print(f"Aviso: {file} não encontrado")
    
    # Mudar para o diretório de build
    os.chdir(build_dir)
    
    # Comando do PyInstaller (modificado para usar o módulo)
    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name", output_name,
        "--onefile",                    # Criar um único arquivo
        "--noconsole",                  # Não mostrar console
        "--add-data", "config;config",  # Incluir diretório config
        "--add-data", "core;core",      # Incluir diretório core
        "--add-data", "utils;utils",    # Incluir diretório utils
        "--add-data", "assets;assets",  # Incluir diretório assets
        "--icon", "assets/icons/app_icon.ico" if (build_dir / "assets/icons/app_icon.ico").exists() else None,
        "main.py"
    ]
    
    # Remover None do comando
    pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if cmd is not None]
    
    print("\nExecutando PyInstaller com os seguintes parâmetros:")
    print(" ".join(pyinstaller_cmd))
    
    # Executar PyInstaller
    result = subprocess.run(pyinstaller_cmd)
    
    if result.returncode == 0:
        print("\nExecutável criado com sucesso!")
        
        # Copiar o executável para o diretório raiz
        exe_path = build_dir / "dist" / f"{output_name}.exe"
        dst_path = current_dir / f"{output_name}.exe"
        
        if exe_path.exists():
            shutil.copy2(exe_path, dst_path)
            print(f"Executável copiado para: {dst_path}")
        else:
            print(f"Aviso: Executável não encontrado em {exe_path}")
    else:
        print("\nErro ao criar o executável!")
    
    # Voltar para o diretório original
    os.chdir(current_dir)
    
    # Limpar diretório de build
    print("\nLimpando arquivos temporários...")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    print("\nProcesso concluído!")

if __name__ == "__main__":
    main()