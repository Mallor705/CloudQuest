# Obter diretório atual do script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Passo 1: Solicitar o caminho do executável do jogo
$ExecutablePath = (Read-Host "Digite o caminho completo do executável do jogo (ex.: D:\Games\Steam\steamapps\common\Jogo\jogo.exe)").Trim('"')
if (-not (Test-Path $ExecutablePath)) {
    Write-Host "Executável não encontrado. Finalizando..."
    exit 1
}
$exeFolder = Split-Path -Parent $ExecutablePath

# Passo 2: Buscar o arquivo steam_appid.txt na pasta do executável
$steamAppIdPath = Join-Path $exeFolder "steam_appid.txt"
if (Test-Path $steamAppIdPath) {
    # Lê todo o conteúdo do arquivo, remove caracteres não numéricos e pega a primeira sequência de dígitos
    $rawContent = Get-Content $steamAppIdPath -Raw
    $appID = [regex]::Match($rawContent, '\d+').Value
    
    if (-not [string]::IsNullOrEmpty($appID)) {
        Write-Host "AppID lido do steam_appid.txt: $appID"
    } else {
        Write-Warning "Nenhum AppID válido encontrado em $steamAppIdPath"
        $appID = Read-Host "Digite manualmente o AppID do jogo"
    }
} else {
    Write-Warning "Arquivo steam_appid.txt não encontrado em $exeFolder"
    $appID = Read-Host "Digite manualmente o AppID do jogo"
}

# Passo 3: Consultar a API Steam (apenas para AppIDs válidos)
try {
    $apiUrl = "https://store.steampowered.com/api/appdetails?appids=$appID"
    $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop

    if ($response.$appID.success -eq $true) {
        $data = $response.$appID.data
        $GameName = $data.name
        Write-Host "Nome do jogo obtido da API: $GameName"
    } else {
        Write-Warning "AppID $appID não encontrado na Steam. Insira o nome manualmente."
        $GameName = Read-Host "Digite o nome do jogo"
    }
} catch {
    Write-Warning "Erro na API Steam: $($_.Exception.Message)"
    $GameName = Read-Host "Digite o nome do jogo manualmente"
}

# Passo 4: Solicitar as demais configurações do usuário
$RclonePath = (Read-Host "Digite o caminho do Rclone (ex.: D:\messi\Documents\rclone\rclone.exe)").Trim('"')
# Nova lógica para determinar o Cloud Remote automaticamente via rclone.conf
$rcloneConfPath = Join-Path $env:APPDATA "rclone\rclone.conf"
if (Test-Path $rcloneConfPath) {
    $confContent = Get-Content $rcloneConfPath
    $remotes = @()
    foreach ($line in $confContent) {
        if ($line -match '^\[(.+)\]') {
            $remotes += $Matches[1]
        }
    }
    if ($remotes.Count -eq 0) {
        Write-Warning "Nenhum remote encontrado no rclone.conf."
        $CloudRemote = Read-Host "Digite o nome do Cloud Remote (ex.: onedrive)"
    } elseif ($remotes.Count -eq 1) {
        $CloudRemote = $remotes[0]
        Write-Host "Cloud Remote encontrado automaticamente: $CloudRemote"
    } else {
        Write-Host "Remotes encontrados:"
        for ($i = 0; $i -lt $remotes.Count; $i++) {
            Write-Host "${i}: $($remotes[$i])"
        }
        $indexInput = Read-Host "Digite o índice do remote desejado"
        $indexParsed = 0
        if ([int]::TryParse($indexInput, [ref]$indexParsed) -and $indexParsed -ge 0 -and $indexParsed -lt $remotes.Count) {
            $CloudRemote = $remotes[$indexParsed]
        } else {
            Write-Warning "Índice inválido. Solicitando entrada manual."
            $CloudRemote = Read-Host "Digite o nome do Cloud Remote (ex.: onedrive)"
        }
    }
} else {
    Write-Warning "Arquivo rclone.conf não encontrado em $rcloneConfPath."
    $CloudRemote = Read-Host "Digite o nome do Cloud Remote (ex.: onedrive)"
}
$LocalDirInput = (Read-Host "Digite o diretório local (ex.: $env:APPDATA\EldenRing)").Trim('"') # Diretório local padrão

# Expandir variáveis de ambiente e normalizar o caminho
$LocalDir = [System.Environment]::ExpandEnvironmentVariables($LocalDirInput)

# Verificar se o caminho é relativo e converter para absoluto
if (-not [System.IO.Path]::IsPathRooted($LocalDir)) {
    $LocalDir = Join-Path -Path (Get-Location) -ChildPath $LocalDir
}

# Verificar existência do diretório
if (-not (Test-Path $LocalDir)) {
    Write-Warning "Diretório não encontrado: $LocalDir"
    $choice = Read-Host "Deseja criar este diretório? (S/N)"
    if ($choice -match '^[Ss]') {
        New-Item -Path $LocalDir -ItemType Directory -Force | Out-Null
        Write-Host "Diretório criado: $LocalDir"
    } else {
        Write-Host "Por favor, insira o caminho novamente."
        $LocalDir = (Read-Host "Digite o diretório local").Trim('"')
        $LocalDir = [System.Environment]::ExpandEnvironmentVariables($LocalDir)
    }
}

$CloudDir = ("CloudQuest/" + (Split-Path $LocalDir -Leaf)).Trim('"')    # Diretório remoto padrão

# Definir o nome do processo utilizando o nome do executável sem extensão
$GameProcess = [System.IO.Path]::GetFileNameWithoutExtension($ExecutablePath)
# Perguntar se o nome do processo está correto
$confirm = Read-Host "O nome do processo detectado é '$GameProcess'. Está correto? (S/N)"
if ($confirm -notmatch '^[Ss]') {
    $GameProcess = Read-Host "Digite o nome correto do processo do jogo"
}

# Passo 5: Exibir as configurações e salvar em um arquivo JSON na pasta config
Write-Host "`nConfigurações:"
Write-Host "Executável: $ExecutablePath"
Write-Host "Pasta do Executável: $exeFolder"
Write-Host "AppID: $appID"
Write-Host "GameName: $GameName"
Write-Host "RclonePath: $RclonePath"
Write-Host "CloudRemote: $CloudRemote"
Write-Host "CloudDir: $CloudDir"
Write-Host "LocalDir: $LocalDir"
Write-Host "GameProcess: $GameProcess"

$config = @{
    ExecutablePath = $ExecutablePath;
    ExeFolder      = $exeFolder;
    AppID          = $appID;
    GameName       = $GameName;
    RclonePath     = $RclonePath;
    CloudRemote    = $CloudRemote;
    CloudDir       = $CloudDir;
    LocalDir       = $LocalDir;
    GameProcess    = $GameProcess
}

# Caminho para a pasta "config" (na raiz do projeto, ao lado de "src" e "assets")
$configDir = Join-Path -Path (Resolve-Path "$PSScriptRoot\..") -ChildPath "profiles"

# Cria a pasta "config" se ela não existir
if (-not (Test-Path -Path $configDir)) {
    New-Item -Path $configDir -ItemType Directory -Force | Out-Null
    Write-Host "Pasta 'config' criada em: $configDir"
}

# Cria/salva o arquivo de perfil JSON
$configFilePath = Join-Path -Path $configDir -ChildPath "$GameName.json"
$config | ConvertTo-Json -Depth 3 | Out-File -FilePath $configFilePath -Encoding UTF8
Write-Host "`nConfigurações salvas em: $configFilePath"

# Criação do atalho na Área de Trabalho
$desktopPath = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path -Path $desktopPath -ChildPath "$GameName.lnk"
$batPath = Join-Path -Path $PSScriptRoot -ChildPath "CloudQuest.bat"

if (Test-Path $batPath) {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $batPath             # Caminho do arquivo .bat
    $shortcut.Arguments = "`"$GameName`""       # Adapte conforme sua necessidade
    $shortcut.WorkingDirectory = $exeFolder     # Diretório de trabalho do jogo
    $shortcut.IconLocation = $ExecutablePath    # Opcional: ícone do jogo
    $shortcut.Save()
    Write-Host "Atalho criado em: $shortcutPath"
} else {
    Write-Warning "CloudQuest.bat não encontrado em $PSScriptRoot"
}