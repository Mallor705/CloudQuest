# CONFIGURAÇÃO DE LOG (UTF-8)
# ====================================================
$ScriptDir = $PSScriptRoot
# Ajusta o caminho para o diretório raiz do projeto
$CloudQuestRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogPath = Join-Path -Path (Join-Path -Path $CloudQuestRoot -ChildPath "logs") -ChildPath "CloudQuest.log"

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

# CONFIGURAÇÕES DO USUÁRIO
$ProfileName = (Get-Content -Path "$env:temp\CloudQuest_Profile.txt" -ErrorAction Stop).Trim() 
Write-Log -Message "Perfil recebido: '$ProfileName'"
# $ProfileName = $args[0] # Captura a primeira tag passada como argumento
$configPath = Join-Path -Path (Resolve-Path "$PSScriptRoot\..\..\profiles") -ChildPath "$ProfileName.json"

if (-not $ProfileName -or "") {
    Write-Log -Message "Nenhum perfil foi especificado." -Level Error
    throw "Erro: Nome do perfil ausente."
}

# Verifique o caminho gerado (para depuração):
Write-Log -Message "Procurando perfil em: $configPath" -Level Info
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

# Exporta a função Write-Log para uso externo
Export-ModuleMember -Function Write-Log
# Adicionado: exportar variáveis de configuração para outros módulos
Export-ModuleMember -Variable RclonePath, CloudRemote, CloudDir, LocalDir, GameProcess, GameName, LauncherExePath