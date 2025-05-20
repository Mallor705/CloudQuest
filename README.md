# QuestConfig

QuestConfig é uma ferramenta para configurar jogos para o CloudQuest. Permite automatizar a configuração de sincronização de saves de jogos usando o Rclone.

## Recursos

- Consulta informações de jogos na Steam
- Detecta localizações de saves automaticamente
- Integra com o PCGamingWiki para obter informações sobre localizações de saves
- Configura sincronização usando Rclone
- Cria atalhos na área de trabalho para facilitar o acesso aos jogos

## Requisitos

- Python 3.6 ou superior
- Bibliotecas: requests, tkinter, psutil, watchdog, pywin32 (Windows)
- Rclone instalado e configurado no sistema

## Instalação

### Método 1: Instalação em modo desenvolvimento

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/CloudQuest.git
cd CloudQuest

# Instalar em modo desenvolvimento
pip install -e .

# Executar o aplicativo
questconfig
```

### Método 2: Execução direta

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/CloudQuest.git
cd CloudQuest

# Executar diretamente (a partir do diretório do projeto)
python -m QuestConfig.ui.app
```

## Uso

1. Abra o QuestConfig através do comando `questconfig` ou pelo método direto
2. Na aba "Informações do Jogo":
   - Adicione o Steam UID (opcional)
   - Selecione o executável do jogo
   - Detecte ou insira o AppID da Steam
   - Forneça o nome do jogo
3. Na aba "Configuração Rclone":
   - Configure o caminho do Rclone
   - Selecione o remote do Rclone
   - Defina o diretório local dos saves (pode ser detectado automaticamente)
   - Configure o diretório cloud
   - Adicione o nome do processo do jogo
4. Na aba "Finalizar":
   - Revise as configurações no resumo
   - Selecione se deseja criar um atalho na área de trabalho
   - Salve a configuração

## Integração com PCGamingWiki

A ferramenta integra-se com o PCGamingWiki para obter informações sobre localizações de saves de jogos. Esta integração possui duas abordagens:

1. **API Query** - Usa a API do PCGamingWiki para buscar informações dos jogos
2. **WikiText Parser** - Um método mais avançado que extrai e processa o texto wiki quando a API não retorna resultados satisfatórios

Para cada jogo, o sistema:
- Busca a página do jogo usando o AppID da Steam
- Extrai informações sobre localizações de saves para Windows, macOS e Linux
- Processa e expande caminhos com variáveis de ambiente e templates
- Valida quais caminhos existem no sistema atual

## Arquitetura

O projeto segue os princípios SOLID:

1. **Single Responsibility**: Cada classe tem uma responsabilidade única
2. **Open/Closed**: As classes são abertas para extensão, fechadas para modificação
3. **Liskov Substitution**: As implementações seguem estritamente as interfaces
4. **Interface Segregation**: Interfaces específicas para cada tipo de serviço
5. **Dependency Inversion**: Componentes dependem de abstrações, não de implementações concretas

A estrutura do projeto é organizada em:

- **interfaces**: Define contratos para serviços
- **core**: Contém lógica de negócios e modelo de domínio
- **services**: Implementações dos serviços
- **ui**: Interface gráfica do usuário
- **utils**: Utilitários gerais

## Licença

[MIT](LICENSE)
