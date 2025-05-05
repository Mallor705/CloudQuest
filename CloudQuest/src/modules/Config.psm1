# CONFIGURAÇÃO DE LOG (UTF-8)
# ====================================================
$ScriptDir = $PSScriptRoot
$LogPath = Join-Path -Path $ScriptDir -ChildPath "logs\CloudQuest.log"

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

# Exporta a função Write-Log para uso externo
Export-ModuleMember -Function Write-Log
 
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
    # As variáveis (RclonePath, CloudRemote, CloudDir, LocalDir, etc.) estão corretamente definidas.
} else {
    Write-Log -Message "Arquivo de configuração do usuário não encontrado." -Level Warning
    throw "Arquivo de configuração do usuário não encontrado."
}