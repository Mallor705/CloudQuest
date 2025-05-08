#!/usr/bin/env python3
# CloudQuest - Gerador de atalhos Steam

import os
import sys
import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Gerar comandos para atalhos Steam para o CloudQuest')
    parser.add_argument('--exe', required=True, help='Caminho completo para o executável CloudQuest.exe')
    parser.add_argument('--profile', help='Nome do perfil específico (opcional)')
    
    args = parser.parse_args()
    
    exe_path = Path(args.exe)
    if not exe_path.exists():
        print(f"ERRO: O executável não foi encontrado: {exe_path}")
        sys.exit(1)
    
    # Verificar diretório de perfis (deve estar junto com o executável em caso de empacotamento)
    profiles_dir = exe_path.parent / "config" / "profiles"
    
    if not profiles_dir.exists():
        # Tente a estrutura de desenvolvimento
        profiles_dir = Path.cwd() / "config" / "profiles"
        if not profiles_dir.exists():
            print(f"ERRO: Diretório de perfis não encontrado: {profiles_dir}")
            sys.exit(1)
    
    # Lista de perfis a processar
    profiles_to_process = []
    
    if args.profile:
        # Perfil específico
        profile_path = profiles_dir / f"{args.profile}.json"
        if not profile_path.exists():
            print(f"ERRO: Perfil não encontrado: {profile_path}")
            sys.exit(1)
        profiles_to_process.append(profile_path)
    else:
        # Todos os perfis
        for profile_file in profiles_dir.glob("*.json"):
            profiles_to_process.append(profile_file)
    
    if not profiles_to_process:
        print("Nenhum perfil encontrado para processar.")
        sys.exit(1)
    
    print("\n===== INSTRUÇÕES PARA ATALHOS STEAM =====\n")
    
    for profile_path in profiles_to_process:
        profile_name = profile_path.stem
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            game_name = profile_data.get('GameName', profile_name)
            exec_path = profile_data.get('ExecutablePath', '')
            
            game_dir = Path(exec_path).parent if exec_path else "???"
            
            print(f"=== {game_name} ({profile_name}) ===")
            print("1. Na Steam, clique com botão direito no jogo > Propriedades")
            print("2. Em 'Destino', insira:")
            print(f'   "{exe_path}" "{profile_name}"')
            print("3. Em 'Iniciar em', insira:")
            print(f'   "{game_dir}"')
            print("\nIsso fará com que o CloudQuest seja executado antes do jogo,")
            print("baixando seus saves, e depois enviando-os para a nuvem ao fechar o jogo.\n")
            
        except Exception as e:
            print(f"ERRO ao processar perfil {profile_name}: {str(e)}")
    
    print("Observações importantes:")
    print("- Certifique-se de que o Rclone esteja configurado corretamente")
    print("- Teste os atalhos antes de usar em seus jogos principais")
    print("- Faça backup manual de seus saves antes de usar o CloudQuest pela primeira vez")

if __name__ == "__main__":
    main()