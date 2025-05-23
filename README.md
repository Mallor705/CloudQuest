# CloudQuest

CloudQuest é uma aplicação Python projetada para simplificar a configuração de jogos e a sincronização de seus arquivos de salvamento (saves) entre múltiplos dispositivos. Ele utiliza o [Rclone](https://rclone.org/) para interagir com diversos serviços de armazenamento em nuvem.

## Sobre a Aplicação

O CloudQuest combina duas funcionalidades principais em uma única solução coesa:

1.  **Sincronizador de Saves (CloudQuest Core)**: O coração da aplicação, responsável por:
    *   Fazer o download dos saves da nuvem antes de iniciar um jogo.
    *   Fazer o upload dos saves para a nuvem após o jogo ser fechado.
    *   Monitorar o processo do jogo.
2.  **Interface de Configuração (QuestConfig)**: Uma interface gráfica amigável (GUI) que permite aos usuários:
    *   Adicionar e gerenciar perfis de jogos.
    *   Configurar caminhos de executáveis de jogos, locais de salvamento e diretórios na nuvem.
    *   Detectar automaticamente informações de jogos (ex: AppID do Steam).
    *   Criar atalhos para facilitar o lançamento de jogos com sincronização.


## 🌟 Recursos Principais

*   **🔄 Sincronização Automática e Bidirecional**:
    *   Upload automático dos saves após fechar o jogo.
    *   Download automático dos saves mais recentes antes de iniciar o jogo.
    *   Suporte a uma vasta gama de serviços de nuvem através do Rclone (Google Drive, Dropbox, OneDrive, etc.).
*   **🖥️ Interface de Configuração Intuitiva (QuestConfig)**:
    *   Gerenciamento fácil de múltiplos perfis de jogos.
    *   Assistente para configuração de novos jogos.
    *   Auto-detecção de AppID do Steam para facilitar a configuração.
    *   Busca de informações sobre locais de save na PCGamingWiki.
    *   Criação de atalhos personalizados na área de trabalho (Windows) ou scripts (Linux/macOS) para iniciar jogos com sincronização.
*   **⚙️ Núcleo Confiável**:
    *   Monitoramento preciso do processo do jogo para garantir que a sincronização ocorra no momento certo.
    *   Sistema de logging detalhado para troubleshooting.
    *   Tratamento de erros e tentativas de sincronização.
*   **📦 Compilação Simplificada**:
    *   Script `cloudquest_compiler.py` para empacotar a aplicação e a interface de configuração em um único executável usando PyInstaller.
*   **🐧 Suporte Multiplataforma**:
    *   Funciona em Windows, Linux e macOS (a interface gráfica e a criação de atalhos podem ter funcionalidades específicas por plataforma).
    *   Script de instalação (`install.sh`) para Linux e macOS.

## ⚙️ Pré-requisitos

*   **Rclone**: É essencial ter o [Rclone](https://rclone.org/downloads/) instalado e configurado com pelo menos um "remote" (serviço de nuvem). O CloudQuest não instala o Rclone.
*   **Sistema Operacional**:
    *   Windows 10 ou superior.
    *   Distribuições Linux recentes.
    *   macOS.
*   **(Para Desenvolvimento/Compilação)**:
    *   Python 3.7 ou superior.
    *   Dependências listadas em `cloudquest_compiler.py` (PyInstaller, Pillow, psutil, requests, watchdog).

## 📥 Instalação

### Windows

1.  Baixe o arquivo `.zip` da release mais recente.
2.  Extraia o conteúdo para um diretório de sua preferência (ex: `C:\CloudQuest`).
3.  Execute `CloudQuest.exe --config` ou diretamente `CloudQuest.exe` (que abrirá a interface de configuração) para começar a configurar seus jogos.

### Linux/macOS

1.  Baixe o arquivo `.tar.gz` ou `.zip` da release mais recente, ou clone o repositório.
2.  Extraia o conteúdo.
3.  Navegue até o diretório extraído e execute o script de instalação:
    ```bash
    cd CloudQuest
    chmod +x install.sh
    ./install.sh
    ```
    O script tentará instalar o CloudQuest em `$HOME/.local/bin` e criar um link simbólico em `/usr/local/bin`.

## 🕹 Como Usar

### 1. Configuração Inicial (Interface Gráfica - QuestConfig)

**Importante**: Para que o CloudQuest localize corretamente os saves, o jogo deve ter sido executado ao menos uma vez para que seus diretórios de saves existam em seu sistema.

**Importante**: Certifique-se de que você já configurou um "remote" no Rclone antes desta etapa.

1.  Inicie a interface de configuração:
    *   **Windows**: Execute `CloudQuest.exe` ou `CloudQuest.exe --config`.
    *   **Linux**: Execute `cloudquest` ou `cloudquest --config` no terminal.
2.  Na interface do QuestConfig:
    *   **Adicionar Novo Perfil**: Clique para criar uma nova configuração para um jogo.
    *   **Caminho do Executável**: Selecione o arquivo executável principal do jogo.
    *   **Steam AppID**: Insira o AppID Steam do jogo (mesmo que não seja da Steam), se for um jogo Steam basta detectar automaticamente.
    *   **Nome do Jogo**: Defina um nome para o perfil.
    *   **Caminho dos Saves**:
        *   Pode ser detectado automaticamente (usando Steam AppID ou buscando na PCGamingWiki).
        *   Pode ser inserido manualmente.
    *   **Configuração Rclone**:
        *   Selecione o "remote" do Rclone previamente configurado. 
        *   Defina o caminho na nuvem onde os saves deste jogo serão armazenados (ex: `meuDrive:/CloudSaves/NomeDoJogo`).
    *   **Opções Adicionais**:
        *   Configure o nome do processo do jogo (geralmente o nome do executável).
        *   Crie um atalho (Windows) ou script de inicialização.
3.  Salve o perfil.

### 2. Sincronizar e Jogar

Após configurar um perfil:

*   **Usando Atalho/Script**: Se você criou um atalho (Windows) ou script durante a configuração, basta executá-lo.
*   **Linha de Comando**:
    ```bash
    # Windows
    CloudQuest.exe "Nome do Perfil"

    # Linux/macOS
    cloudquest "Nome do Perfil"
    ```
    Substitua `"Nome do Perfil"` pelo nome exato que você deu ao perfil do jogo na configuração.

O CloudQuest irá:
1.  Baixar os saves mais recentes da nuvem.
2.  Iniciar o jogo.
3.  Aguardar o jogo ser fechado.
4.  Fazer upload dos saves atualizados para a nuvem.

### Argumentos de Linha de Comando (`CloudQuest.exe` ou `cloudquest`)

*   `[nome_do_perfil]`: (Opcional) Inicia o jogo com o perfil especificado e sincroniza os saves.
*   `--config` ou `-c`: Abre a interface de configuração (QuestConfig).
*   `--game-path CAMINHO_DO_JOGO` ou `-g CAMINHO_DO_JOGO`: (Opcional, usado em conjunto com `nome_do_perfil`) Especifica o caminho do diretório do jogo.
*   `--silent` ou `-s`: (Opcional) Executa em modo silencioso, suprimindo diálogos de interface gráfica (útil para scripts).

Se nenhum argumento for fornecido e nenhum perfil temporário for encontrado, a interface de configuração será iniciada.

## 🛠️ Desenvolvimento e Compilação

### Estrutura do Projeto

O projeto é dividido em dois componentes principais, cada um com sua própria estrutura, visando a separação de responsabilidades (Single Responsibility Principle) e a extensibilidade:

*   **`CloudQuest/`**: O núcleo da aplicação, responsável pela lógica de sincronização.
    *   `core/`: Contém a lógica central (SRP).
        *   `profile_manager.py`: Gerencia o carregamento e manipulação de perfis (SRP).
        *   `sync_manager.py`: Lida com as operações de sincronização via Rclone (SRP).
        *   `game_launcher.py`: Responsável por iniciar e monitorar os processos dos jogos (SRP).
    *   `utils/`: Utilitários compartilhados (logging, paths).
    *   `config/`: Módulos relacionados à configuração base da aplicação.
    *   `main.py`: Ponto de entrada e orquestrador do fluxo da aplicação CloudQuest (SRP).

*   **`QuestConfig/`**: A interface gráfica para configuração de jogos.
    *   `core/`: Lógica de negócios e modelos de dados da interface de configuração.
    *   `services/`: Camada de serviço, abstraindo fontes de dados e lógica complexa (Interface Segregation Principle, Dependency Inversion Principle).
        *   `config_service.py`: Gerencia a leitura e escrita de perfis.
        *   `game_info_service.py`: Busca informações de jogos (Steam, PCGamingWiki).
        *   `shortcut_service.py`: Cria atalhos.
    *   `ui/`: Componentes da interface do usuário (Views, Widgets) (SRP).
        *   `app.py`: Ponto de entrada da aplicação QuestConfig GUI.
        *   `views.py`: Define as janelas e layouts principais.
    *   `utils/`: Utilitários específicos do QuestConfig.

*   **`assets/`**: Recursos gráficos (ícones, etc.).
*   **`dist/`**: Diretório de saída para executáveis compilados.
*   **`cloudquest_compiler.py`**: Script para compilar a aplicação usando PyInstaller.
*   **`app.py`**: Ponto de entrada principal que determina se executa o CloudQuest core ou o QuestConfig.
*   **`install.sh`**: Script de instalação para Linux/macOS.

Este design promove baixo acoplamento e alta coesão, facilitando a manutenção e a adição de novas funcionalidades (Open/Closed Principle). As interfaces implícitas e a separação clara de preocupações ajudam a seguir o Liskov Substitution Principle e o Dependency Inversion Principle.

### Compilando a partir do Código-Fonte

1.  Clone o repositório:
    ```bash
    git clone https://github.com/seu-usuario/CloudQuest.git # Substitua pelo URL correto do seu repositório
    cd CloudQuest
    ```
2.  Instale as dependências de compilação (principalmente PyInstaller e outras listadas no `cloudquest_compiler.py`):
    ```bash
    pip install pyinstaller Pillow psutil requests watchdog
    ```
3.  Execute o script de compilação:
    ```bash
    python cloudquest_compiler.py
    ```
    O executável será gerado no diretório `dist/CloudQuest/`.

## 📝 Notas Técnicas

*   Os perfis de configuração dos jogos são armazenados como arquivos JSON no diretório `CloudQuest/config/profiles/` (dentro da estrutura do projeto) ou em um local apropriado para dados de aplicação dependendo da instalação (ex: `~/.config/CloudQuest/profiles` em Linux). O local exato pode variar com a forma de execução (script vs. executável).
*   Os logs são armazenados no diretório `logs/`.

## ⚠️ Aviso

CloudQuest é um projeto em desenvolvimento. Embora testado, podem existir bugs. Use por sua conta e risco. Backups regulares dos seus saves são sempre uma boa prática.

## ❓ Suporte e Contribuições

*   Reporte problemas ou sugira funcionalidades através das [Issues do GitHub](https://github.com/seu-usuario/CloudQuest/issues). # Substitua pelo URL correto do seu repositório
*   Contribuições são bem-vindas! Faça um fork do projeto e envie um Pull Request.

## 🙏 Créditos e Reconhecimentos

*   **[Rclone](https://rclone.org/)**: Pela ferramenta essencial que torna possível a sincronização com diversos serviços de nuvem.
*   **[PCGamingWiki](https://www.pcgamingwiki.com/)**: Pela sua vasta base de dados pública sobre jogos, que auxilia na detecção de caminhos de saves.
*   **CustomTkinter**: Pela excelente biblioteca para criação de interfaces gráficas modernas em Python.
*   Comunidade de desenvolvimento Python e Open Source.

## 📜 Licença

Este projeto é licenciado sob a GNU General Public License v3.0. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes. 
