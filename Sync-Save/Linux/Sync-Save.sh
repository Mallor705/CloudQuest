#!/bin/bash

# Configurações
CLOUD_REMOTE="onedrive"
CLOUD_DIR="SaveGames/EldenRing"
LOCAL_DIR_LINUX="$HOME/.local/share/Steam/steamapps/compatdata/2932237219/pfx/drive_c/users/steamuser/AppData/Roaming/EldenRing"
GAME_PROCESS_NAME="eldenring.exe"

# Criar diretórios se não existirem
mkdir -p "$LOCAL_DIR_LINUX" || { echo "Erro ao criar diretório local"; exit 1; }
rclone mkdir "$CLOUD_REMOTE:$CLOUD_DIR" || { echo "Erro ao criar diretório remoto"; exit 1; }

# Função para sincronização inteligente
sync_saves() {
    echo "Sincronizando saves..."
    
    # Fase 1: Trazer alterações da nuvem
    rclone copy "$CLOUD_REMOTE:$CLOUD_DIR/" "$LOCAL_DIR_LINUX/" \
        --progress \
        --update \
        --create-empty-src-dirs || { echo "Erro ao baixar da nuvem"; exit 1; }
    
    # Fase 2: Enviar alterações locais
    rclone copy "$LOCAL_DIR_LINUX/" "$CLOUD_REMOTE:$CLOUD_DIR/" \
        --progress \
        --update \
        --create-empty-src-dirs || { echo "Erro ao enviar para a nuvem"; exit 1; }
}

# Etapa 1: Sincronização inicial
sync_saves

# Etapa 2: Aguardar o jogo iniciar
echo "Aguardando o jogo ser iniciado..."
while ! pgrep -x "$GAME_PROCESS_NAME" > /dev/null; do
    sleep 5
done

# Etapa 3: Aguardar o jogo fechar
echo "Aguardando o jogo fechar..."
while pgrep -x "$GAME_PROCESS_NAME" > /dev/null; do
    sleep 10
done

# Pequena pausa para garantir que arquivos estejam liberados
sleep 5

# Etapa 4: Sincronização final bidirecional
sync_saves

# Mantém o terminal aberto
read -p "Pressione Enter para sair..."