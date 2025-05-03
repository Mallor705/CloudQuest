# ER_Sync.ps1
# Versão 4.0 - Notificações na Bandeja do Sistema

# Configurações
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"

# Verificar modo de execução
if (-not [Environment]::UserInteractive) {
    Write-Warning "Execute este script diretamente (não como serviço)!"
    exit 1
}

# Carregar biblioteca para notificações
Add-Type -AssemblyName System.Windows.Forms

# Configurar ícone na bandeja
$script:notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
$notifyIcon.Visible = $true

# Função de notificação na bandeja
function Show-BalloonTip {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "Info"
    )

    $notifyIcon.BalloonTipTitle = $Title
    $notifyIcon.BalloonTipText = $Message
    $notifyIcon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::$Type
    $notifyIcon.ShowBalloonTip(3000)
    Start-Sleep -Seconds 2
}

# Criar diretório local
if (-not (Test-Path -Path $LocalDir)) {
    try {
        New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
        Show-BalloonTip -Title "Sync-Save" -Message "Diretório local criado" -Type "Info"
    }   
    catch {
        Show-BalloonTip -Title "ERRO Sync-Save" -Message "Falha ao criar diretório: $_" -Type "Error"
        exit 1
    }
}

# Função Rclone oculta
function Invoke-RcloneCommand {
    param($Arguments)
    $process = Start-Process -FilePath $RclonePath -ArgumentList $Arguments -PassThru -WindowStyle Hidden -Wait
    if ($process.ExitCode -ne 0) {
        throw "Erro Rclone (Código $($process.ExitCode))"
    }
}

# Processo de sincronização
function Sync-Saves {
    Show-BalloonTip -Title "Sync-Save" -Message "Iniciando sincronização..." -Type "Info"
    
    try {
        # Download da nuvem
        Invoke-RcloneCommand "copy `"$($CloudRemote):$($CloudDir)/`" `"$LocalDir/`" --update --create-empty-src-dirs"
        # Upload para nuvem
        Invoke-RcloneCommand "copy `"$LocalDir/`" `"$($CloudRemote):$($CloudDir)/`" --update --create-empty-src-dirs"
        Show-BalloonTip -Title "Sync-Save" -Message "Sincronização concluída" -Type "Info"
    }
    catch {
        Show-BalloonTip -Title "ERRO Sync-Save" -Message "Falha na sincronização: $_" -Type "Error"
        exit 1
    }
}

# Execução principal
try {
    Sync-Saves
    
    # Iniciar jogo
    Show-BalloonTip -Title "Sync-Save" -Message "Iniciando Elden Ring..." -Type "Info"
    Start-Process -FilePath $GameExePath -PassThru
    
    # Monitorar processo
    while ($null -ne (Get-Process -Name $GameProcess -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 5
    }

    Sync-Saves
    Show-BalloonTip -Title "Sync-Save" -Message "Processo finalizado" -Type "Info"
}
catch {
    Show-BalloonTip -Title "ERRO Fatal" -Message "$_" -Type "Error"
    exit 1
}
finally {
    # Limpeza
    $notifyIcon.Visible = $false
    $notifyIcon.Dispose()
}