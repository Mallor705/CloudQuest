# ER_Sync.ps1
# Versão Completa: Sincronização + Log + Notificações Personalizadas

# CONFIGURAÇÕES DO USUÁRIO
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"
$LogPath = "$env:APPDATA\Sync-Save.log"

# INICIALIZAÇÃO DO SISTEMA
# ---------------------------------------------------------------------------------------
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# CONFIGURAÇÃO DO LOG
"`n=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===" | Out-File -FilePath $LogPath -Append

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    $logEntry | Out-File -FilePath $LogPath -Append
}

# NOTIFICAÇÕES PERSONALIZADAS
# ---------------------------------------------------------------------------------------
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info"  # info, success, error
    )

    # Configuração de cores
    $colors = @{
        "info"    = [System.Drawing.Color]::FromArgb(45,125,255)   # Azul
        "success" = [System.Drawing.Color]::FromArgb(40,167,69)    # Verde
        "error"   = [System.Drawing.Color]::FromArgb(220,53,69)    # Vermelho
    }

    # Criar formulário
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.Size = New-Object System.Drawing.Size(350, 80)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Location = New-Object System.Drawing.Point(
        [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width - 370,
        [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Height - 90
    )
    $form.TopMost = $true

    # Painel principal
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock = [System.Windows.Forms.DockStyle]::Fill
    $panel.BackColor = $colors[$Type]
    $form.Controls.Add($panel)

    # Ícone
    $iconBox = New-Object System.Windows.Forms.PictureBox
    $iconBox.Size = New-Object System.Drawing.Size(32, 32)
    $iconBox.Location = New-Object System.Drawing.Point(15, 20)
    $iconBox.Image = if ($Type -eq "error") { [System.Drawing.SystemIcons]::Error.ToBitmap() } else { [System.Drawing.SystemIcons]::Information.ToBitmap() }
    $panel.Controls.Add($iconBox)

    # Textos
    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::White
    $lblTitle.Location = New-Object System.Drawing.Point(60, 15)
    $lblTitle.Size = New-Object System.Drawing.Size(270, 20)
    $lblTitle.Text = $Title
    $panel.Controls.Add($lblTitle)

    $lblMessage = New-Object System.Windows.Forms.Label
    $lblMessage.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $lblMessage.ForeColor = [System.Drawing.Color]::White
    $lblMessage.Location = New-Object System.Drawing.Point(60, 35)
    $lblMessage.Size = New-Object System.Drawing.Size(270, 40)
    $lblMessage.Text = $Message
    $panel.Controls.Add($lblMessage)

    # Temporizador
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 3000
    $timer.Add_Tick({ $form.Close(); $timer.Dispose() })
    $timer.Start()

    Write-Log -Message "$Title - $Message" -Level $Type
    $form.ShowDialog()
}

# FUNÇÕES PRINCIPAIS
# ---------------------------------------------------------------------------------------
function Invoke-RcloneCommand {
    param($Source, $Destination)

    $arguments = @(
        "copy",
        "`"$Source`"",
        "`"$Destination`"",
        "--update",
        "--create-empty-src-dirs",
        "--stats=0",
        "--log-level=ERROR"
    )

    Write-Log -Message "Executando: rclone $($arguments -join ' ')" -Level Info

    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $RclonePath
    $processInfo.Arguments = $arguments
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

    if (-not [string]::IsNullOrEmpty($output)) {
        Write-Log -Message "Saída do Rclone: $output" -Level Info
    }

    if ($process.ExitCode -ne 0) {
        Write-Log -Message "Erro Rclone (Código $($process.ExitCode)): $errorOutput" -Level Error
        throw "Erro durante a sincronização"
    }
}

function Sync-Saves {
    try {
        Show-CustomNotification -Title "Sincronização" -Message "Iniciando sincronização de saves..." -Type "info"
        
        # Download da nuvem
        Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir
        
        # Upload para nuvem
        Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/"
        
        Show-CustomNotification -Title "Sincronização" -Message "Sincronização concluída!" -Type "success"
    }
    catch {
        Show-CustomNotification -Title "Erro de Sincronização" -Message "Falha durante a sincronização" -Type "error"
        exit 1
    }
}

# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------------------------------------
try {
    # Criar diretório se necessário
    if (-not (Test-Path -Path $LocalDir)) {
        try {
            New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
            Show-CustomNotification -Title "Configuração" -Message "Diretório local criado" -Type "success"
        }
        catch {
            Show-CustomNotification -Title "Erro Crítico" -Message "Falha ao criar diretório" -Type "error"
            exit 1
        }
    }

    # Sincronização inicial
    Sync-Saves

    # Iniciar jogo
    Show-CustomNotification -Title "Execução" -Message "Iniciando Elden Ring..." -Type "info"
    $gameProcess = Start-Process -FilePath $GameExePath -PassThru
    Write-Log -Message "Processo do jogo iniciado (PID: $($gameProcess.Id))" -Level Info

    # Monitorar processo
    Write-Log -Message "Monitorando execução do jogo..." -Level Info
    while ($null -ne (Get-Process -Name $GameProcess -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 5
    }

    # Sincronização final
    Sync-Saves
    Show-CustomNotification -Title "Conclusão" -Message "Processo finalizado com sucesso!" -Type "success"
}
catch {
    Write-Log -Message "ERRO FATAL: $($_.Exception.Message)" -Level Error
    Show-CustomNotification -Title "Erro Fatal" -Message "Ocorreu um erro crítico" -Type "error"
}
finally {
    Write-Log -Message "=== Sessão finalizada ===`n" -Level Info
}