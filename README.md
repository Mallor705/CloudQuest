# CloudQuest

Automatiza a sincronização bidirecional dos arquivos de save de jogos entre um diretório local e um armazenamento em nuvem, utilizando o **rclone**.

*Sincronize seus saves de jogos com a nuvem de forma transparente*

---

## 📦 Funcionalidades
- **Sincronização bidirecional** entre diretório local e nuvem
- Interface gráfica para configuração de jogos (`questconfig.exe`)
- Detecção automática de AppID da Steam
- Criação de atalhos personalizados na área de trabalho
- Suporte a múltiplos provedores de nuvem (via rclone)
- Logs detalhados de operações

## ⚙️ Pré-requisitos
- [Rclone](https://rclone.org/) instalado e configurado com pelo menos 1 remote
- Windows 10 ou superior
- .NET Framework 4.8 (já incluído na maioria das instalações do Windows)

## 📥 Instalação
1. Baixe os arquivos `cloudquest.exe` e `questconfig.exe`
2. Coloque-os em um diretório permanente (ex: `C:\CloudQuest`)
3. Execute `questconfig.exe` para começar a configurar seus jogos

## 🕹 Como Usar
### Configuração Inicial (`questconfig.exe`)
1. Execute `questconfig.exe`
2. Na aba **1. Executável e AppID**:
   - Selecione o executável do jogo
   - Detecte/insira o AppID da Steam
3. Na aba **2. Configuração Rclone**:
   - Selecione o remote configurado
   - Defina diretórios local e na nuvem
4. Na aba **3. Finalizar**:
   - Revise o resumo
   - Salve a configuração

### Sincronização (`cloudquest.exe`)
- Execute o atalho criado na área de trabalho para iniciar o jogo com sincronização automática
- A sincronização ocorrerá:
  - Antes de iniciar o jogo (download da nuvem)
  - Após fechar o jogo (upload para nuvem)

## 🛠 Notas Técnicas
- Os perfis de configuração são armazenados em `config/profiles/`
- Logs são gerados em `logs/questconfig.log`
- Formatos suportados de nuvem: Qualquer serviço configurável no rclone (Google Drive, Dropbox, OneDrive, etc)
- Diretório padrão de saves locais: `Documents/CloudQuest/[Nome do Jogo]`

## ❓ Suporte
Reporte problemas no [GitHub Issues](https://github.com/Mallor705/CloudQuest/issues)

---

**📄 Licença**  
 GNU GENERAL PUBLIC LICENSE - Consulte o arquivo [LICENSE](LICENSE) para detalhes