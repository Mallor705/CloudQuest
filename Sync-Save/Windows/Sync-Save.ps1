# ER_Sync.ps1
# Versão com Log Detalhado

# Configurações
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"
$LogPath = "$env:APPDATA\Sync-Save.log"  # Caminho do arquivo de log

# Configuração inicial do log
"`n=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===" | Out-File -FilePath $LogPath -Append

# Função de log avançada
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Escrever no arquivo de log
    $logEntry | Out-File -FilePath $LogPath -Append
    
    # Escrever no console (apenas se executado interativamente)
    if ([Environment]::UserInteractive) {
        $color = @{
            'Info' = 'White'
            'Warning' = 'Yellow'
            'Error' = 'Red'
        }[$Level]
        Write-Host $logEntry -ForegroundColor $color
    }
}

# Carregar biblioteca para notificações
Add-Type -AssemblyName System.Windows.Forms

# Configurar ícone na bandeja
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
$notifyIcon.Visible = $true

# Função de notificação com log
function Show-Notification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "Info"
    )

    Write-Log -Message "$Title - $Message" -Level $Type
    $notifyIcon.BalloonTipTitle = $Title
    $notifyIcon.BalloonTipText = $Message
    $notifyIcon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::$Type
    $notifyIcon.ShowBalloonTip(3000)
}

# Criar diretório local
if (-not (Test-Path -Path $LocalDir)) {
    try {
        Write-Log -Message "Tentando criar diretório local: $LocalDir"
        New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
        Show-Notification -Title "Sync-Save" -Message "Diretório local criado"
        Write-Log -Message "Diretório local criado com sucesso" -Level Info
    }   
    catch {
        Write-Log -Message "Falha ao criar diretório: $_" -Level Error
        Show-Notification -Title "ERRO Sync-Save" -Message "Falha ao criar diretório" -Type "Error"
        $notifyIcon.Dispose()
        exit 1
    }
}

# Função Rclone com log detalhado
function Invoke-RcloneCommand {
    param($Arguments)
    
    Write-Log -Message "Executando Rclone: $RclonePath $Arguments"
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $RclonePath
    $processInfo.Arguments = $Arguments
    $processInfo.RedirectStandardError = $true
    $processInfo.RedirectStandardOutput = $true
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    
    $output = $process.StandardOutput.ReadToEnd()
    $errorOutput = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    
    Write-Log -Message "Saída do Rclone:`n$output" -Level Info
    if (-not [string]::IsNullOrEmpty($errorOutput)) {
        Write-Log -Message "Erro do Rclone:`n$errorOutput" -Level Error
    }
    
    if ($process.ExitCode -ne 0) {
        throw "Código de erro: $($process.ExitCode)"
    }
}

# Processo de sincronização
function Sync-Saves {
    Write-Log -Message "Iniciando processo de sincronização" -Level Info
    Show-Notification -Title "Sync-Save" -Message "Iniciando sincronização..."
    
    try {
        # Fase de download
        Write-Log -Message "Sincronizando nuvem -> local" -Level Info
        Invoke-RcloneCommand "copy `"$($CloudRemote):$($CloudDir)/`" `"$LocalDir/`" --update --create-empty-src-dirs --log-format=json"
        
        # Fase de upload
        Write-Log -Message "Sincronizando local -> nuvem" -Level Info
        Invoke-RcloneCommand "copy `"$LocalDir/`" `"$($CloudRemote):$($CloudDir)/`" --update --create-empty-src-dirs --log-format=json"
        
        Show-Notification -Title "Sync-Save" -Message "Sincronização concluída"
        Write-Log -Message "Sincronização finalizada com sucesso" -Level Info
    }
    catch {
        Write-Log -Message "Falha na sincronização: $_" -Level Error
        Show-Notification -Title "ERRO Sync-Save" -Message "Falha na sincronização" -Type "Error"
        $notifyIcon.Dispose()
        exit 1
    }
}

# Execução principal
try {
    Sync-Saves
    
    # Iniciar jogo
    Write-Log -Message "Iniciando processo do jogo: $GameExePath" -Level Info
    Show-Notification -Title "Sync-Save" -Message "Iniciando Elden Ring..."
    $game = Start-Process -FilePath $GameExePath -PassThru
    Write-Log -Message "Processo do jogo iniciado (PID: $($game.Id))" -Level Info
    
    # Monitoramento
    Write-Log -Message "Monitorando processo do jogo..." -Level Info
    do {
        Start-Sleep -Seconds 5
        $process = Get-Process -Name $GameProcess -ErrorAction SilentlyContinue
    } while ($process)
    
    Write-Log -Message "Processo do jogo finalizado" -Level Info
    
    # Sincronização pós-jogo
    Sync-Saves
    Show-Notification -Title "Sync-Save" -Message "Processo finalizado"
    Write-Log -Message "Processo completo finalizado com sucesso" -Level Info
}
catch {
    Write-Log -Message "ERRO FATAL: $_" -Level Error
    Write-Log -Message "Stack Trace: $($_.ScriptStackTrace)" -Level Error
    Show-Notification -Title "ERRO Fatal" -Message "Ocorreu um erro crítico" -Type "Error"
}
finally {
    # Limpeza e log final
    Write-Log -Message "Finalizando recursos..."
    $notifyIcon.Visible = $false
    $notifyIcon.Dispose()
    Write-Log -Message "=== Sessão finalizada ===" -Level Info
}