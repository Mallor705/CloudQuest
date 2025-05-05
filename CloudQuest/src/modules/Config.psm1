# CONFIGURAÇÃO DE LOG (UTF-8)
# ====================================================
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

Set-Content -Path $LogPath -Value "=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===`n" -Encoding UTF8

# CONFIGURAÇÕES DO SCRIPT   
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LogPath = Join-Path -Path $ScriptDir -ChildPath "Sync-Save.log"

# CONFIGURAÇÕES DO USUÁRIO
# ====================================================
$configPath = Join-Path -Path $ScriptDir -ChildPath "UserConfig.json"
if (Test-Path $configPath) {
    $userConfig = Get-Content -Path $configPath -Raw | ConvertFrom-Json
    $RclonePath = $userConfig.RclonePath
    $CloudRemote = $userConfig.CloudRemote
    $CloudDir = $userConfig.CloudDir
    $LocalDir = $userConfig.LocalDir
    $GameProcess = $userConfig.GameProcess
    $GameName = $userConfig.GameName
    $LauncherExePath = $userConfig.ExecutablePath
} else {
    Write-Log -Message "Arquivo de configuração do usuário não encontrado." -Level Warning
    exit 1
}