# CloudQuest

Automatiza a sincronização bidirecional dos arquivos de save de jogos entre um diretório local e um armazenamento em nuvem, utilizando o **rclone**.

*Sincronize seus saves de jogos com a nuvem de forma transparente*

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

**📄 Licença**  
 GNU GENERAL PUBLIC LICENSE - Consulte o arquivo [LICENSE](LICENSE) para detalhes
