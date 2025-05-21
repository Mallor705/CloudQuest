#!/bin/bash

# install.sh - Script para instalar o CloudQuest

# Cores para output
GREEN='\\033[0;32m'
YELLOW='\\033[0;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

# Função para printar mensagens
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Verifica se o script está sendo executado com sudo
check_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        log_error "Este script não deve ser executado como root diretamente. Permissões de sudo serão solicitadas quando necessário."
        exit 1
    fi
}

# Função para verificar dependências do sistema
check_system_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Dependência não encontrada: $1. Por favor, instale-a e tente novamente."
        if [[ "$1" == "python3" ]]; then
            log_info "Você pode tentar: sudo apt install python3 python3-pip (Debian/Ubuntu) ou sudo pacman -S python python-pip (Arch)"
        elif [[ "$1" == "git" ]]; then
            log_info "Você pode tentar: sudo apt install git (Debian/Ubuntu) ou sudo pacman -S git (Arch)"
        elif [[ "$1" == "pip" ]]; then
            log_info "Você pode tentar: sudo apt install python3-pip (Debian/Ubuntu) ou sudo pacman -S python-pip (Arch). Certifique-se que é o pip para python3."
        fi
        exit 1
    fi
    log_info "Dependência encontrada: $1"
}

# Função principal de instalação
main() {
    check_sudo

    log_info "Iniciando a instalação do CloudQuest..."
    echo

    # Verificar dependências do sistema
    log_info "Verificando dependências do sistema..."
    check_system_dependency "git"
    check_system_dependency "python3"
    check_system_dependency "pip" # pip pode ser pip3 em alguns sistemas
    echo

    log_warn "Lembre-se: O CloudQuest requer que o Rclone (https://rclone.org/downloads/) esteja instalado e configurado no seu sistema."
    log_warn "Este script não instalará o Rclone por você."
    read -p "Pressione Enter para continuar se o Rclone já estiver configurado, ou CTRL+C para sair e configurá-lo."
    echo

    # Determinar o diretório do projeto
    # Se o script estiver dentro de um repo git e na raiz, usa o dir atual.
    # Caso contrário, clona o repositório.
    PROJECT_DIR=$(pwd)
    CLONED_TEMP=false

    if [ -d ".git" ]; then
        log_info "Detectado repositório Git. Usando o diretório atual: $PROJECT_DIR"
    else
        log_info "Nenhum repositório Git detectado no diretório atual."
        # Tenta usar um diretório temporário para o clone
        # Isso é mais seguro se o usuário baixou apenas o script
        PROJECT_DIR=$(mktemp -d -t cloudquest-install-XXXXXX)
        CLONED_TEMP=true
        log_info "Clonando o repositório CloudQuest para $PROJECT_DIR..."
        if git clone https://github.com/Mallor705/CloudQuest.git "$PROJECT_DIR"; then
            log_info "Repositório clonado com sucesso."
            cd "$PROJECT_DIR" || { log_error "Não foi possível entrar no diretório do projeto $PROJECT_DIR"; exit 1; }
        else
            log_error "Falha ao clonar o repositório. Verifique sua conexão e o URL do repositório."
            rm -rf "$PROJECT_DIR"
            exit 1
        fi
    fi
    echo

    # Instalar dependências Python
    log_info "Instalando dependências Python..."
    # Lista de dependências do cloudquest.py
    PYTHON_DEPS=("PyInstaller" "Pillow" "psutil" "requests" "watchdog")
    
    # Verifica se existe requirements.txt, senão instala uma por uma
    if [ -f "requirements.txt" ]; then
        log_info "Encontrado requirements.txt. Instalando dependências..."
        if pip install -r requirements.txt; then
            log_info "Dependências Python instaladas com sucesso via requirements.txt."
        else
            log_error "Falha ao instalar dependências Python via requirements.txt. Verifique o arquivo e seu ambiente pip."
            if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi
            exit 1
        fi
    else
        log_warn "requirements.txt não encontrado. Tentando instalar dependências individualmente: ${PYTHON_DEPS[*]}"
        for dep in "${PYTHON_DEPS[@]}"; do
            log_info "Instalando $dep..."
            if pip install "$dep"; then
                log_info "$dep instalado com sucesso."
            else
                log_error "Falha ao instalar $dep. Verifique seu ambiente pip."
                if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi
                exit 1
            fi
        done
    fi
    echo

    # # Compilar o projeto
    # log_info "Compilando o CloudQuest..."
    # if python3 cloudquest.py; then
    #     log_info "CloudQuest compilado com sucesso!"
    # else
    #     log_error "Falha na compilação do CloudQuest. Verifique os logs acima."
    #     if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi
    #     exit 1
    # fi
    # echo

    # COMPILED_EXEC="dist/CloudQuest/CloudQuest" # Sem .exe para Linux

    # if [ ! -f "$COMPILED_EXEC" ]; then
    #     log_error "Executável compilado não encontrado em $COMPILED_EXEC."
    #     if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi
    #     exit 1
    # fi

    # Instalar o executável
    log_info "Tentando instalar o CloudQuest..."
    
    INSTALL_PATH_USER="$HOME/.local/bin"
    INSTALL_PATH_SYSTEM="/usr/local/bin"
    FINAL_EXEC_PATH=""

    # Tenta instalar no diretório local do usuário primeiro
    log_info "Tentando instalar para o usuário atual em $INSTALL_PATH_USER..."
    mkdir -p "$INSTALL_PATH_USER"
    
    if cp "$COMPILED_EXEC" "$INSTALL_PATH_USER/cloudquest" && chmod +x "$INSTALL_PATH_USER/cloudquest"; then
        log_info "CloudQuest instalado com sucesso em $INSTALL_PATH_USER/cloudquest"
        FINAL_EXEC_PATH="$INSTALL_PATH_USER/cloudquest"
        
        # Verificar se $INSTALL_PATH_USER está no PATH
        if [[ ":$PATH:" != *":$INSTALL_PATH_USER:"* ]]; then
            log_warn "$INSTALL_PATH_USER não está no seu PATH."
            SHELL_CONFIG_FILE=""
            # Extrai o nome base do shell (ex: /bin/zsh -> zsh)
            CURRENT_SHELL=$(basename "$SHELL")

            if [ "$CURRENT_SHELL" = "bash" ]; then
                SHELL_CONFIG_FILE="$HOME/.bashrc"
            elif [ "$CURRENT_SHELL" = "zsh" ]; then
                SHELL_CONFIG_FILE="$HOME/.zshrc"
            elif [ "$CURRENT_SHELL" = "fish" ]; then
                SHELL_CONFIG_FILE="$HOME/.config/fish/config.fish"
            fi

            if [ -n "$SHELL_CONFIG_FILE" ]; then
                # Para fish, o diretório pode não existir, então criamos
                if [ "$CURRENT_SHELL" = "fish" ]; then
                    mkdir -p "$(dirname "$SHELL_CONFIG_FILE")"
                    # Cria o arquivo se não existir para fish
                    touch "$SHELL_CONFIG_FILE"
                fi

                if [ -f "$SHELL_CONFIG_FILE" ]; then
                    log_info "Tentando adicionar $INSTALL_PATH_USER ao PATH em $SHELL_CONFIG_FILE..."
                    if [ "$CURRENT_SHELL" = "fish" ]; then
                        # Para fish, usamos fish_add_path que é idempotente
                        if ! grep -q "fish_add_path \"$INSTALL_PATH_USER\"" "$SHELL_CONFIG_FILE"; then
                            echo "" >> "$SHELL_CONFIG_FILE"
                            echo "# Adicionado pelo instalador do CloudQuest" >> "$SHELL_CONFIG_FILE"
                            echo "fish_add_path \"$INSTALL_PATH_USER\"" >> "$SHELL_CONFIG_FILE"
                            log_info "$INSTALL_PATH_USER adicionado ao PATH em $SHELL_CONFIG_FILE usando fish_add_path."
                            log_warn "Para aplicar as mudanças, recarregue a configuração do seu shell (execute 'source $SHELL_CONFIG_FILE') ou abra um novo terminal."
                        else
                            log_info "$INSTALL_PATH_USER já parece estar configurado em $SHELL_CONFIG_FILE (via fish_add_path)."
                        fi
                    else
                        # Para bash/zsh, verifica a linha export exata
                        if ! grep -Fxq "export PATH=\"$INSTALL_PATH_USER:\$PATH\"" "$SHELL_CONFIG_FILE"; then
                            echo "" >> "$SHELL_CONFIG_FILE"
                            echo "# Adicionado pelo instalador do CloudQuest para incluir $INSTALL_PATH_USER" >> "$SHELL_CONFIG_FILE"
                            echo "export PATH=\"$INSTALL_PATH_USER:\$PATH\"" >> "$SHELL_CONFIG_FILE"
                            log_info "$INSTALL_PATH_USER adicionado ao PATH em $SHELL_CONFIG_FILE."
                            log_warn "Para aplicar as mudanças, recarregue a configuração do seu shell (ex: 'source $SHELL_CONFIG_FILE') ou abra um novo terminal."
                        else
                            log_info "$INSTALL_PATH_USER já parece estar configurado em $SHELL_CONFIG_FILE."
                        fi
                    fi
                else
                    log_warn "Arquivo de configuração do shell $SHELL_CONFIG_FILE não encontrado (mesmo após tentativa de criação para fish)."
                fi
            else
                if [ -n "$SHELL_CONFIG_FILE" ]; then
                    log_warn "Arquivo de configuração do shell $SHELL_CONFIG_FILE não encontrado."
                else
                    log_warn "Não foi possível determinar automaticamente o arquivo de configuração do seu shell ($CURRENT_SHELL)."
                fi
                log_warn "Para usar o comando 'cloudquest' diretamente, adicione a seguinte linha ao seu arquivo de configuração do shell:"
                log_warn "  export PATH=\"$INSTALL_PATH_USER:\$PATH\""
                log_warn "Depois, recarregue seu shell ou abra um novo terminal."
            fi
        else
            log_info "$INSTALL_PATH_USER já está no seu PATH."
        fi
    else
        log_warn "Falha ao instalar em $INSTALL_PATH_USER. Talvez permissões?"
        log_info "Tentando instalar para todos os usuários em $INSTALL_PATH_SYSTEM (requer sudo)..."
        
        if sudo cp "$COMPILED_EXEC" "$INSTALL_PATH_SYSTEM/cloudquest" && sudo chmod +x "$INSTALL_PATH_SYSTEM/cloudquest"; then
            log_info "CloudQuest instalado com sucesso em $INSTALL_PATH_SYSTEM/cloudquest"
            FINAL_EXEC_PATH="$INSTALL_PATH_SYSTEM/cloudquest"
            log_info "Você pode executar o CloudQuest com o comando: cloudquest"
        else
            log_error "Falha ao instalar em $INSTALL_PATH_SYSTEM mesmo com sudo."
            log_error "A instalação falhou. Verifique as permissões e os logs."
            if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi
            exit 1
        fi
    fi
    echo

    # Limpeza se clonado temporariamente
    if [ "$CLONED_TEMP" = true ]; then
        log_info "Removendo diretório temporário $PROJECT_DIR..."
        rm -rf "$PROJECT_DIR"
    fi

    log_info "${GREEN}Instalação do CloudQuest concluída!${NC}"
    if [ -n "$FINAL_EXEC_PATH" ]; then
         log_info "Executável: $FINAL_EXEC_PATH"
    fi
    log_info "Use o comando 'cloudquest --config' para iniciar a configuração ou 'cloudquest NOME_DO_PERFIL' para jogar."
}

# Executa a função principal
main 