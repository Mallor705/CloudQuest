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
            log_info "Você pode tentar: sudo apt install python3 (Debian/Ubuntu) ou sudo pacman -S python (Arch)"
        elif [[ "$1" == "git" ]]; then
            log_info "Você pode tentar: sudo apt install git (Debian/Ubuntu) ou sudo pacman -S git (Arch)"
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
    check_system_dependency "git" # Necessário para clonar, se aplicável
    # python3 e pip não são mais estritamente necessários para instalar um binário pré-compilado,
    # mas python3 pode ser útil para outros scripts do usuário ou se o binário tiver alguma ligação inesperada.
    # Manter a verificação do python3 por enquanto.
    check_system_dependency "python3" 
    echo

    log_warn "Lembre-se: O CloudQuest requer que o Rclone (https://rclone.org/downloads/) esteja instalado e configurado no seu sistema."
    log_warn "Este script não instalará o Rclone por você."
    read -p "Pressione Enter para continuar se o Rclone já estiver configurado, ou CTRL+C para sair e configurá-lo."
    echo

    # Determinar o diretório do projeto
    PROJECT_DIR=$(pwd)
    CLONED_TEMP=false

    if [ -d ".git" ]; then
        log_info "Detectado repositório Git. Usando o diretório atual: $PROJECT_DIR"
    else
        log_info "Nenhum repositório Git detectado no diretório atual. Assumindo que o executável está neste diretório ou em 'dist/'."
        # Se o usuário baixou um ZIP/tarball com o binário, ele estará aqui.
        # Não vamos clonar se não for um repo git, pois o objetivo é instalar um binário baixado.
    fi
    echo

    # Local do executável pré-compilado
    # Ajuste COMPILED_EXEC_NAME conforme o nome do seu executável
    COMPILED_EXEC_NAME="CloudQuest" # Assumindo que é 'CloudQuest' para Linux/macOS
    
    # Tenta encontrar o executável em locais comuns
    # Se o usuário descompactou o release, pode estar em ./dist/CloudQuest/CloudQuest ou ./CloudQuest etc.
    POSSIBLE_EXEC_PATHS=(
        "$PROJECT_DIR/dist/$COMPILED_EXEC_NAME/$COMPILED_EXEC_NAME" # Estrutura comum do PyInstaller --onedir
        "$PROJECT_DIR/dist/$COMPILED_EXEC_NAME"                   # Estrutura comum do PyInstaller --onefile
        "$PROJECT_DIR/$COMPILED_EXEC_NAME"                        # Se o executável estiver na raiz do PWD
    )

    COMPILED_EXEC=""
    for path_candidate in "${POSSIBLE_EXEC_PATHS[@]}"; do
        if [ -f "$path_candidate" ]; then
            COMPILED_EXEC="$path_candidate"
            log_info "Executável encontrado em: $COMPILED_EXEC"
            break
        fi
    done

    if [ -z "$COMPILED_EXEC" ]; then
        log_error "Executável '$COMPILED_EXEC_NAME' não encontrado nos caminhos esperados."
        log_info "Verifique se o executável está em $PROJECT_DIR/dist/$COMPILED_EXEC_NAME/, $PROJECT_DIR/dist/, ou $PROJECT_DIR/"
        exit 1
    fi
    echo
    
    # Instalar o executável
    log_info "Tentando instalar o CloudQuest a partir de $COMPILED_EXEC..."
    
    INSTALL_PATH_USER="$HOME/.local/bin"
    INSTALL_PATH_SYSTEM="/usr/local/bin"
    FINAL_EXEC_NAME="cloudquest" # Nome do comando final
    FINAL_EXEC_PATH=""

    # Tenta instalar no diretório local do usuário primeiro
    log_info "Tentando instalar para o usuário atual em $INSTALL_PATH_USER..."
    mkdir -p "$INSTALL_PATH_USER"
    
    if cp -f "$COMPILED_EXEC" "$INSTALL_PATH_USER/$FINAL_EXEC_NAME" && chmod +x "$INSTALL_PATH_USER/$FINAL_EXEC_NAME"; then
        log_info "CloudQuest instalado com sucesso em $INSTALL_PATH_USER/$FINAL_EXEC_NAME"
        FINAL_EXEC_PATH="$INSTALL_PATH_USER/$FINAL_EXEC_NAME"
        
        # Verificar se $INSTALL_PATH_USER está no PATH
        if [[ ":$PATH:" != *":$INSTALL_PATH_USER:"* ]]; then
            log_warn "$INSTALL_PATH_USER não está no seu PATH."
            SHELL_CONFIG_FILE=""
            CURRENT_SHELL=$(basename "$SHELL")

            if [ "$CURRENT_SHELL" = "bash" ]; then
                SHELL_CONFIG_FILE="$HOME/.bashrc"
            elif [ "$CURRENT_SHELL" = "zsh" ]; then
                SHELL_CONFIG_FILE="$HOME/.zshrc"
            elif [ "$CURRENT_SHELL" = "fish" ]; then
                SHELL_CONFIG_FILE="$HOME/.config/fish/config.fish"
            fi

            if [ -n "$SHELL_CONFIG_FILE" ]; then
                if [ "$CURRENT_SHELL" = "fish" ]; then
                    mkdir -p "$(dirname "$SHELL_CONFIG_FILE")"
                    touch "$SHELL_CONFIG_FILE"
                fi

                if [ -f "$SHELL_CONFIG_FILE" ]; then
                    log_info "Tentando adicionar $INSTALL_PATH_USER ao PATH em $SHELL_CONFIG_FILE..."
                    if [ "$CURRENT_SHELL" = "fish" ]; then
                        if ! grep -q "fish_add_path \\"$INSTALL_PATH_USER\\"" "$SHELL_CONFIG_FILE"; then
                            echo "" >> "$SHELL_CONFIG_FILE"
                            echo "# Adicionado pelo instalador do CloudQuest" >> "$SHELL_CONFIG_FILE"
                            echo "fish_add_path \\"$INSTALL_PATH_USER\\"" >> "$SHELL_CONFIG_FILE"
                            log_info "$INSTALL_PATH_USER adicionado ao PATH em $SHELL_CONFIG_FILE usando fish_add_path."
                            log_warn "Para aplicar as mudanças, recarregue a configuração do seu shell (execute 'source $SHELL_CONFIG_FILE') ou abra um novo terminal."
                        else
                            log_info "$INSTALL_PATH_USER já parece estar configurado em $SHELL_CONFIG_FILE (via fish_add_path)."
                        fi
                    else
                        if ! grep -Fxq "export PATH=\\"$INSTALL_PATH_USER:\\$PATH\\"" "$SHELL_CONFIG_FILE"; then
                            echo "" >> "$SHELL_CONFIG_FILE"
                            echo "# Adicionado pelo instalador do CloudQuest para incluir $INSTALL_PATH_USER" >> "$SHELL_CONFIG_FILE"
                            echo "export PATH=\\"$INSTALL_PATH_USER:\\$PATH\\"" >> "$SHELL_CONFIG_FILE"
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
                log_warn "Para usar o comando '$FINAL_EXEC_NAME' diretamente, adicione a seguinte linha ao seu arquivo de configuração do shell:"
                log_warn "  export PATH=\\"$INSTALL_PATH_USER:\\$PATH\\""
                log_warn "Depois, recarregue seu shell ou abra um novo terminal."
            fi
        else
            log_info "$INSTALL_PATH_USER já está no seu PATH."
        fi
    else
        log_warn "Falha ao instalar em $INSTALL_PATH_USER. Talvez permissões?"
        log_info "Tentando instalar para todos os usuários em $INSTALL_PATH_SYSTEM (requer sudo)..."
        
        if sudo cp -f "$COMPILED_EXEC" "$INSTALL_PATH_SYSTEM/$FINAL_EXEC_NAME" && sudo chmod +x "$INSTALL_PATH_SYSTEM/$FINAL_EXEC_NAME"; then
            log_info "CloudQuest instalado com sucesso em $INSTALL_PATH_SYSTEM/$FINAL_EXEC_NAME"
            FINAL_EXEC_PATH="$INSTALL_PATH_SYSTEM/$FINAL_EXEC_NAME"
            log_info "Você pode executar o CloudQuest com o comando: $FINAL_EXEC_NAME"
        else
            log_error "Falha ao instalar em $INSTALL_PATH_SYSTEM mesmo com sudo."
            log_error "A instalação falhou. Verifique as permissões e os logs."
            if [ "$CLONED_TEMP" = true ]; then rm -rf "$PROJECT_DIR"; fi # Limpa se clonou, embora clonagem esteja desativada para este caso de uso
            exit 1
        fi
    fi
    echo

    # Limpeza se clonado temporariamente (não deve acontecer neste fluxo)
    if [ "$CLONED_TEMP" = true ]; then
        log_info "Removendo diretório temporário $PROJECT_DIR..."
        rm -rf "$PROJECT_DIR"
    fi

    log_info "${GREEN}Instalação do CloudQuest concluída!${NC}"
    if [ -n "$FINAL_EXEC_PATH" ]; then
         log_info "Executável: $FINAL_EXEC_PATH"
    fi
    log_info "Use o comando '$FINAL_EXEC_NAME --config' para iniciar a configuração ou '$FINAL_EXEC_NAME NOME_DO_PERFIL' para jogar."
}

# Ponto de entrada do script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 