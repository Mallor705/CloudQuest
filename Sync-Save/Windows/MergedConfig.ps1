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
    $appID = (Get-Content $steamAppIdPath | ForEach-Object { $_.Trim() })
    Write-Host "AppID lido do steam_appid.txt: $appID"
} else {
    Write-Warning "Arquivo steam_appid.txt não encontrado em $exeFolder"
    $appID = Read-Host "Digite manualmente o AppID do jogo"
}

# Passo 3: Consultar a API Steam para obter informações do jogo
try {
    $apiUrl = "https://store.steampowered.com/api/appdetails?appids=$appID"
    $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
    if ($response.$appID.success) {
        $data = $response.$appID.data
        $GameName = $data.name
        Write-Host "Nome do jogo obtido da API: $GameName"
    } else {
        Write-Warning "Dados não disponíveis para AppID $appID"
        $GameName = Read-Host "Digite o nome do jogo"
    }
} catch {
    Write-Warning "Erro ao buscar dados na API Steam: $_"
    $GameName = Read-Host "Digite o nome do jogo"
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
$LocalDir = (Read-Host "Digite o diretório local (ex.: $env:APPDATA\EldenRing)").Trim('"')
$CloudDir = (Read-Host "Digite o diretório no Cloud (ex.: SaveGames/EldenRing)").Trim('"')


# Definir o nome do processo utilizando o nome do executável sem extensão
$GameProcess = [System.IO.Path]::GetFileNameWithoutExtension($ExecutablePath)

# Passo 5: Exibir as configurações e salvar em um arquivo JSON na pasta do executável
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

$configFilePath = Join-Path -Path $ScriptDir -ChildPath "UserConfig.json"
$config | ConvertTo-Json -Depth 3 | Out-File -FilePath $configFilePath -Encoding UTF8
Write-Host "`nConfigurações salvas em: $configFilePath"