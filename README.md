# CloudQuest

CloudQuest é uma aplicação Python para configurar jogos e sincronizar seus arquivos de salvamento usando Rclone.

## Sobre a aplicação

CloudQuest permite que você sincronize arquivos de salvamento de jogos entre múltiplos dispositivos usando o serviço de nuvem de sua preferência via Rclone. A aplicação agora integra dois componentes em um único executável:

1. **Interface de Configuração**: Interface gráfica para configurar jogos e definir locais de salvamento
2. **Sincronizador de Saves**: Responsável por sincronizar os saves antes e depois de jogar

## Como usar

### Executando a aplicação

A aplicação pode ser executada de várias maneiras:

1. **Modo de Configuração**:
   ```
   CloudQuest.exe --config
   ```
   ou
   ```
   CloudQuest.exe -c
   ```
   Isso inicia a interface de configuração para gerenciar seus jogos.

2. **Sincronizar e Jogar** (com perfil já configurado):
   ```
   CloudQuest.exe nome_do_perfil
   ```
   Isso sincroniza o jogo especificado, executa-o e depois sincroniza novamente.

3. **Modo Interativo** (sem parâmetros):
   ```
   CloudQuest.exe
   ```
   Se não for especificado um perfil, a aplicação iniciará a interface de configuração.

### Fluxo de uso

1. Execute a aplicação em modo de configuração (`CloudQuest.exe --config`)
2. Configure seus jogos:
   - Adicione o caminho executável do jogo
   - Defina o local dos arquivos de salvamento
   - Configure o diretório na nuvem onde os saves serão armazenados
3. Salve a configuração (isso criará um perfil)
4. Para jogar, execute `CloudQuest.exe nome_do_jogo` ou use os atalhos criados

## Requisitos

- Python 3.6 ou superior (apenas para desenvolvimento)
- Rclone instalado e configurado com pelo menos um remote
- Windows, macOS ou Linux

## Desenvolvimento

### Estrutura do projeto

O projeto foi organizado seguindo princípios SOLID:

- **CloudQuest/**: Componente de sincronização
  - **core/**: Lógica principal
  - **utils/**: Utilitários
  - **config/**: Configurações

- **QuestConfig/**: Interface de configuração
  - **core/**: Modelo de domínio e lógica de negócio
  - **interfaces/**: Interfaces para contratos claros
  - **services/**: Implementações de serviços
  - **ui/**: Interface gráfica
  - **utils/**: Utilitários

### Compilando o executável

Para compilar a aplicação em um único executável:

```bash
python cloudquest.py
```

Isso usará PyInstaller para gerar o executável na pasta `dist/CloudQuest/`.

## Aviso

CloudQuest está em desenvolvimento. Use por sua conta e risco.

---

## 🌟 Recursos Principais
### 🔄 Sincronização Bidirecional
- Upload automático após fechar o jogo
- Download pré-execução dos saves mais recentes
- Suporte a qualquer serviço de nuvem via [Rclone](https://rclone.org/)

### 🖥 Interface Inteligente
- Configurador gráfico (`questconfig.exe`)
- Notificações animadas com status de sincronização
- Auto-detecção de AppID Steam
- Gerenciamento de múltiplos perfis de jogos
- Criação de atalhos personalizados na área de trabalho

### ⚙️ Núcleo Avançado
- Monitoramento preciso de processos
- 3 tentativas de sincronização com backoff exponencial
- Sistema de logging detalhado com rotação automática

## ⚙️ Pré-requisitos
- [Rclone](https://rclone.org/) instalado e configurado com pelo menos 1 remote
- Windows 10 ou superior
- .NET Framework 4.8 (já incluído na maioria das instalações do Windows)

## 📥 Instalação
1. Baixe os arquivo `.zip`
2. Extraia em um diretório permanente (ex: `C:\CloudQuest`)
3. Execute `questconfig.exe` para começar a configurar seus jogos

## 🕹 Como Usar
### Configuração Inicial
1. Execute `questconfig.exe`
2. Na aba **1. Executável e AppID**:
   - Selecione o executável do jogo
   - Detecte/insira o AppID da Steam
3. Na aba **2. Configuração Rclone**:
   - Indique a localização de instalação do Rclone.
   - Selecione o remote configurado
   - Defina diretórios local e na nuvem
4. Na aba **3. Finalizar**:
   - Revise o resumo
   - Salve a configuração

### Sincronização
- Execute o atalho criado na área de trabalho para iniciar o jogo com sincronização automática
- A sincronização ocorrerá:
  - Antes de iniciar o jogo (download da nuvem)
  - Após fechar o jogo (upload para nuvem)

## 🛠 Notas Técnicas
- Os perfis de configuração são armazenados em `config/profiles/`
- Formatos suportados de nuvem: Qualquer serviço configurável no rclone (Google Drive, Dropbox, OneDrive, etc)

## ❓ Suporte
Reporte problemas no [GitHub Issues](https://github.com/Mallor705/CloudQuest/issues)

---

## 📝 Créditos e Reconhecimentos

- **[PCGamingWiki](https://www.pcgamingwiki.com/)**  
  Este projeto utiliza a API pública da PCGamingWiki para localizar e identificar os diretórios de saves dos jogos. Agradecemos à comunidade da PCGamingWiki por manter uma base de dados tão completa e aberta.

- **[Rclone](https://rclone.org/)**  
  A sincronização de arquivos com serviços de nuvem é realizada através do Rclone, uma ferramenta open source poderosa para gerenciamento de arquivos em múltiplos provedores de nuvem.

**📜 Licença**  
 GNU GENERAL PUBLIC LICENSE - Consulte o arquivo [LICENSE](LICENSE) para detalhes