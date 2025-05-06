# CONFIGURAÇÃO DE LOG (UTF-8)
# ====================================================
$ScriptDir = $PSScriptRoot

function Initialize-LogSystem {
    param(
        [string]$RootPath
    )
    
    $LogDir = Join-Path -Path $RootPath -ChildPath "logs"
    
    if (-not (Test-Path -Path $LogDir)) {
        New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
    }
    
    $Script:LogPath = Join-Path -Path $LogDir -ChildPath "CloudQuest.log"
    Set-Content -Path $Script:LogPath -Value "=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===`n" -Encoding UTF8
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    $logEntry | Out-File -FilePath $Script:LogPath -Append -Encoding UTF8 -Force
}

# CONFIGURAÇÕES DO USUÁRIO
# ====================================================
function Load-GameProfile {
    param(
        [string]$ProfileName,
        [string]$ProfilesDir
    )

    $profileFile = Join-Path -Path $ProfilesDir -ChildPath "$ProfileName.json"

    # Verifica se o perfil existe
    if (-not (Test-Path $profileFile)) {
        Write-Log -Message "ERRO: Perfil '$ProfileName' não encontrado em: $profileFile" -Level Error
        throw "Perfil de jogo não encontrado: $ProfileName"
    }

    try {
        $userConfig = Get-Content -Path $profileFile -Raw | ConvertFrom-Json
        
        # Configura variáveis globais
        $Script:RclonePath = $userConfig.RclonePath
        $Script:CloudRemote = $userConfig.CloudRemote
        $Script:CloudDir = $userConfig.CloudDir
        $Script:LocalDir = $userConfig.LocalDir
        $Script:GameProcess = $userConfig.GameProcess
        $Script:GameName = $userConfig.GameName
        $Script:LauncherExePath = $userConfig.ExecutablePath
        
        Write-Log -Message "Perfil de jogo '$ProfileName' carregado com sucesso" -Level Info
        
        return $userConfig
    }
    catch {
        Write-Log -Message "ERRO: Falha ao carregar perfil - $_" -Level Error
        throw "Falha ao carregar perfil do jogo: $_"
    }
}

function Get-AvailableProfiles {
    param(
        [string]$ProfilesDir
    )
    
    if (-not (Test-Path $ProfilesDir)) {
        Write-Log -Message "Diretório de perfis não encontrado: $ProfilesDir" -Level Warning
        return @()
    }
    
    $profiles = Get-ChildItem -Path $ProfilesDir -Filter "*.json" | ForEach-Object { $_.BaseName }
    return $profiles
}

# Exporta funções e variáveis
Export-ModuleMember -Function Write-Log, Initialize-LogSystem, Load-GameProfile, Get-AvailableProfiles
Export-ModuleMember -Variable RclonePath, CloudRemote, CloudDir, LocalDir, GameProcess, GameName, LauncherExePath