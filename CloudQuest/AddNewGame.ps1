# Requer versão do PowerShell 5.1 ou superior
#Requires -Version 5.1

<#
.SYNOPSIS
Script para adicionar novos jogos à configuração do CloudQuest

.DESCRIPTION
Coleta informações sobre o jogo, verifica dados na Steam, configura sincronização com Rclone
e cria perfil de configuração com atalho na área de trabalho.
#>

# Configurações iniciais
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Configuração de logs
$ScriptDir = $PSScriptRoot
# Ajusta o caminho para o diretório raiz do projeto
$CloudQuestRoot = Split-Path -Parent $PSScriptRoot
$LogPath = Join-Path -Path (Join-Path -Path $CloudQuestRoot -ChildPath "logs") -ChildPath "AddNewGame.log"

# Cria o diretório de logs se não existir
$logDirectory = Split-Path -Path $LogPath -Parent
if (-not (Test-Path -Path $logDirectory)) {
    New-Item -Path $logDirectory -ItemType Directory -Force | Out-Null
    Write-Host "Diretório de logs criado: $logDirectory"
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8 -Force
}

# Função para exibir cabeçalho estilizado
function Show-Header {
    Write-Host "`n=== CloudQuest Game Configurator ===" -ForegroundColor Cyan
    Write-Host "Versão 2.0 | $(Get-Date -Format 'dd/MM/yyyy HH:mm')`n" -ForegroundColor DarkCyan
    Write-Log -Message "Início da execução do CloudQuest Game Configurator v2.0" -Level INFO
}

# Função para validação de caminhos
function Test-ValidPath {
    param(
        [string]$Path,
        [string]$Type = 'File'
    )
    
    if (-not (Test-Path -Path $Path)) {
        Write-Log -Message "$Type não encontrado: $Path" -Level WARNING
        Write-Warning "$Type não encontrado: $Path"
        return $false
    }
    
    if ($Type -eq 'File' -and -not (Test-Path -Path $Path -PathType Leaf)) {
        Write-Log -Message "O caminho especificado não é um arquivo: $Path" -Level WARNING
        Write-Warning "O caminho especificado não é um arquivo: $Path"
        return $false
    }
    
    return $true
}

# Função para remover acentos de uma string
function Remove-Acentos {
    param([string]$inputString)
    $normalized = $inputString.Normalize([Text.NormalizationForm]::FormD)
    $stringBuilder = New-Object System.Text.StringBuilder
    foreach ($c in $normalized.ToCharArray()) {
        if ([System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($c) -ne [System.Globalization.UnicodeCategory]::NonSpacingMark) {
            $stringBuilder.Append($c) | Out-Null
        }
    }
    return $stringBuilder.ToString()
}


Show-Header

try {
    # Passo 1: Solicitar o caminho do executável do jogo
    Write-Log -Message "Iniciando etapa 1: Coleta do executável" -Level INFO
    do {
        $ExecutablePath = (Read-Host "Digite o caminho completo do executável do jogo (ex.: D:\Games\Steam\steamapps\common\Jogo\jogo.exe)").Trim('"')
        
        if (-not $ExecutablePath.EndsWith('.exe')) {
            Write-Log -Message "Arquivo inválido (não é .exe): $ExecutablePath" -Level WARNING
            Write-Warning "O arquivo deve ser um executável (.exe)"
            continue
        }
        
        if (Test-ValidPath -Path $ExecutablePath -Type 'File') {
            $exeFolder = Split-Path -Parent $ExecutablePath
            Write-Log -Message "Executável válido encontrado: $ExecutablePath" -Level INFO
            break
        }
    } while ($true)

    # Passo 2: Buscar o AppID do jogo
    Write-Log -Message "Iniciando etapa 2: Busca do AppID" -Level INFO
    $steamAppIdPath = Join-Path $exeFolder "steam_appid.txt"
    $appID = $null

    if (Test-ValidPath -Path $steamAppIdPath -Type 'File') {
        try {
            $rawContent = Get-Content $steamAppIdPath -Raw -ErrorAction Stop
            $appID = [regex]::Match($rawContent, '\d{4,}').Value
            
            if ($appID -and $appID -match '^\d+$') {
                Write-Log -Message "AppID detectado: $appID" -Level INFO
                Write-Host "[+] AppID detectado: $appID" -ForegroundColor Green
            }
            else {
                Write-Log -Message "Arquivo steam_appid.txt sem AppID válido" -Level WARNING
                Write-Warning "Nenhum AppID válido encontrado no arquivo"
                throw
            }
        }
        catch {
            Write-Log -Message "Falha ao ler steam_appid.txt: $($_.Exception.Message)" -Level ERROR
            Write-Warning "Falha ao ler steam_appid.txt"
            $appID = $null
        }
    }

    if (-not $appID) {
        Write-Log -Message "Solicitando AppID manualmente" -Level INFO
        do {
            $appID = Read-Host "Digite manualmente o AppID do jogo (somente números)"
        } while (-not ($appID -match '^\d+$'))
        Write-Log -Message "AppID manual inserido: $appID" -Level INFO
    }

    # Passo 3: Consultar a API Steam
    Write-Log -Message "Iniciando etapa 3: Consulta à API Steam" -Level INFO
    $GameName = $null
    $apiUrl = "https://store.steampowered.com/api/appdetails?appids=$appID&l=portuguese"

    try {
        Write-Host "`nConsultando API Steam..." -ForegroundColor DarkGray
        Write-Log -Message "Consultando API Steam em: $apiUrl" -Level INFO
        $response = Invoke-RestMethod -Uri $apiUrl -UserAgent "CloudQuest/2.0" -TimeoutSec 10
        
        if ($response.$appID.success -eq $true -and $response.$appID.data) {
            $GameNameInput = $response.$appID.data.name
            Write-Log -Message "Nome oficial detectado: $GameName" -Level INFO
            Write-Host "[+] Nome oficial detectado: $GameName" -ForegroundColor Green
        }
        else {
            Write-Log -Message "AppID $appID não encontrado ou dados incompletos" -Level WARNING
            Write-Warning "AppID $appID não encontrado ou dados incompletos"
            throw
        }
    }
    catch {
        Write-Log -Message "Falha na consulta à API Steam: $($_.Exception.Message)" -Level ERROR
        Write-Warning "Falha na consulta à API Steam: $($_.Exception.Message)"
        do {
            $GameNameInput = Read-Host "Digite o nome do jogo"
        } while ([string]::IsNullOrWhiteSpace($GameNameInput))
        Write-Log -Message "Nome manual inserido: $GameNameInput" -Level INFO
    }

    $GameName = Remove-Acentos($GameNameInput)  # Remover acentos do nome
    $GameName = $GameName -replace '[^\w\s-]', '_'  # Remover caracteres especiais
    $GameName = $GameName -replace '\s+', '_'  # Substituir espaços por underline
    Write-Log -Message "Nome oficial processado: $GameName" -Level INFO

    # Passo 4: Configurações do Rclone
    Write-Log -Message "Iniciando etapa 4: Configuração do Rclone" -Level INFO
    $RclonePath = $null
    $defaultRclonePath = Join-Path ${env:ProgramFiles} "Rclone\rclone.exe"

    do {
        $inputPath = (Read-Host "Digite o caminho do Rclone [Enter para padrão: $defaultRclonePath]").Trim('"')
        $RclonePath = if ([string]::IsNullOrWhiteSpace($inputPath)) { $defaultRclonePath } else { $inputPath }
        Write-Log -Message "Verificando Rclone em: $RclonePath" -Level INFO
    } while (-not (Test-ValidPath -Path $RclonePath -Type 'File'))

    # Detecção automática de remotes
    $rcloneConfPath = Join-Path $env:APPDATA "rclone\rclone.conf"
    $remotes = @()  # Inicialização garantida como array

    if (Test-ValidPath -Path $rcloneConfPath -Type 'File') {
        try {
            $confContent = Get-Content $rcloneConfPath -ErrorAction Stop
            # Força o resultado a ser um array mesmo com 0 ou 1 elemento
            $remotes = @($confContent | Where-Object { $_ -match '^\s*\[([^\]]+)\]' } | ForEach-Object { $Matches[1] })
            Write-Log -Message "Remotes detectados: $($remotes -join ', ')" -Level INFO
        }
        catch {
            Write-Log -Message "Falha ao ler rclone.conf: $($_.Exception.Message)" -Level ERROR
        }
    }

    if ($remotes.Count -gt 0) {
        Write-Host "`nRemotes disponíveis:" -ForegroundColor Cyan
        $remotes | ForEach-Object { Write-Host "  → $_" }
        
        do {
            $CloudRemote = Read-Host "Digite o nome do remote desejado"
            Write-Log -Message "Tentativa de remote: $CloudRemote" -Level INFO
        } while (-not ($remotes -contains $CloudRemote))
    }
    else {
        Write-Log -Message "Nenhum remote configurado encontrado" -Level WARNING
        Write-Warning "Nenhum remote configurado encontrado"
        do {
            $CloudRemote = Read-Host "Digite o nome do Cloud Remote (ex.: onedrive)"
        } while ([string]::IsNullOrWhiteSpace($CloudRemote))
        Write-Log -Message "Remote manual inserido: $CloudRemote" -Level INFO
    }

    # Passo 5: Configuração de diretórios
    Write-Log -Message "Iniciando etapa 5: Configuração de diretórios" -Level INFO
    $LocalDir = $null
    $defaultLocalDir = Join-Path $env:APPDATA (Split-Path $exeFolder -Leaf)

    do {
        $inputDir = (Read-Host "Digite o diretório local [Enter para padrão: $defaultLocalDir]").Trim('"')
        $LocalDir = if ([string]::IsNullOrWhiteSpace($inputDir)) { $defaultLocalDir } else { $inputDir }
        $LocalDir = [Environment]::ExpandEnvironmentVariables($LocalDir)
        
        if (-not [IO.Path]::IsPathRooted($LocalDir)) {
            $LocalDir = Join-Path (Get-Location).Path $LocalDir
        }
        
        Write-Log -Message "Validando diretório local: $LocalDir" -Level INFO
        
        if (-not (Test-Path $LocalDir)) {
            $choice = Read-Host "Diretório não existe. Criar? (S/N)"
            if ($choice -match '^[Ss]') {
                try {
                    New-Item -Path $LocalDir -ItemType Directory -Force | Out-Null
                    Write-Log -Message "Diretório criado: $LocalDir" -Level INFO
                    Write-Host "Diretório criado: $LocalDir" -ForegroundColor Green
                }
                catch {
                    Write-Log -Message "Falha ao criar diretório: $_" -Level ERROR
                    Write-Warning "Falha ao criar diretório: $_"
                    continue
                }
            }
            else {
                Write-Log -Message "Usuário optou por não criar diretório" -Level INFO
                Write-Host "Por favor, insira um novo caminho"
                continue
            }
        }
        break
    } while ($true)

    $CloudDirLeaf = (Split-Path -Leaf $LocalDir)
    $CloudDir = "CloudQuest/$CloudDirLeaf"
    Write-Log -Message "Diretório cloud definido: $CloudDir" -Level INFO

    # Passo 6: Detecção do processo
    Write-Log -Message "Iniciando etapa 6: Detecção do processo" -Level INFO
    $GameProcess = [IO.Path]::GetFileNameWithoutExtension($ExecutablePath)
    Write-Host "`nProcesso detectado: $GameProcess" -ForegroundColor Cyan
    Write-Log -Message "Processo detectado: $GameProcess" -Level INFO

    do {
        $confirm = Read-Host "Confirmar nome do processo? (S/N)"
        if ($confirm -match '^[Nn]') {
            do {
                $GameProcess = Read-Host "Digite o nome correto do processo"
            } while ([string]::IsNullOrWhiteSpace($GameProcess))
            Write-Log -Message "Processo manual inserido: $GameProcess" -Level INFO
        }
        else {
            break
        }
    } while ($true)

    # Passo 7: Salvar configurações
    Write-Log -Message "Iniciando etapa 7: Salvar configurações" -Level INFO
    $config = [ordered]@{
        ExecutablePath = $ExecutablePath
        ExeFolder      = $exeFolder
        AppID          = $appID
        GameName       = $GameNameInput
        RclonePath     = $RclonePath
        CloudRemote    = $CloudRemote
        CloudDir       = $CloudDir
        LocalDir       = $LocalDir
        GameProcess    = $GameProcess
        LastModified   = (Get-Date -Format 'o')
    }

    $configDir = Join-Path $ScriptDir "..\profiles"
    if (-not (Test-Path $configDir)) {
        New-Item -Path $configDir -ItemType Directory | Out-Null
        Write-Log -Message "Diretório de configurações criado: $configDir" -Level INFO
    }

    $configFile = Join-Path $configDir "$($GameName).json"
    $config | ConvertTo-Json -Depth 3 | Out-File -FilePath $configFile -Encoding utf8
    Write-Log -Message "Configurações salvas em: $configFile" -Level INFO
    Write-Host "`n[✓] Configurações salvas em: $configFile" -ForegroundColor Green

    # Passo 8: Criar atalho
    Write-Log -Message "Iniciando etapa 8: Criação de atalho" -Level INFO
    $desktopPath = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktopPath "$($GameNameInput).lnk"
    $batPath = Join-Path $ScriptDir "CloudQuest.bat"

    if (Test-ValidPath -Path $batPath -Type 'File') {
        try {
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($shortcutPath)
            $shortcut.TargetPath = 'cmd.exe'
            $shortcut.Arguments = "/c `"$batPath`" `"$GameName`""
            $shortcut.WorkingDirectory = $exeFolder
            $shortcut.IconLocation = "$ExecutablePath,0"
            $shortcut.Save()
            Write-Log -Message "Atalho criado: $shortcutPath" -Level INFO
            Write-Host "[✓] Atalho criado: $shortcutPath" -ForegroundColor Green
        }
        catch {
            Write-Log -Message "Erro ao criar atalho: $_" -Level ERROR
            Write-Warning "Erro ao criar atalho: $_"
        }
    }
    else {
        Write-Log -Message "Arquivo CloudQuest.bat não encontrado em: $batPath" -Level ERROR
        Write-Warning "Arquivo CloudQuest.bat não encontrado!"
    }

    Write-Log -Message "Configuração concluída com sucesso" -Level INFO
    Write-Host "`nConfiguração concluída com sucesso!`n" -ForegroundColor Cyan
}
catch {
    Write-Log -Message "Erro fatal: $($_.Exception.Message)" -Level ERROR
    Write-Host "`n[!] Erro durante a execução: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}