# ER_Sync.ps1
# Versão Final: Sincronização + Log UTF-8 + Notificações + Retentativas

# CONFIGURAÇÕES DO USUÁRIO
# ====================================================
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"
$LogPath = "$env:APPDATA\Sync-Save.log"

# INICIALIZAÇÃO DO SISTEMA
# ====================================================
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

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
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

"`n=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===" | Out-File $LogPath -Encoding UTF8

# NOTIFICAÇÕES PERSONALIZADAS
# ====================================================
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info" # info, success, error
    )

    # Configuração de layout
    $formWidth = 300
    $formHeight = 80
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea

    # Criar formulário
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.Size = New-Object System.Drawing.Size($formWidth, $formHeight)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Location = New-Object System.Drawing.Point(
        $screen.Width - $formWidth - 20,
        $screen.Height - $formHeight - 20
    )
    $form.TopMost = $true

    # Configurar cores
    $colors = @{
        "info"    = [System.Drawing.Color]::FromArgb(70,130,180)   # Azul
        "success" = [System.Drawing.Color]::FromArgb(34,139,34)    # Verde
        "error"   = [System.Drawing.Color]::FromArgb(178,34,34)    # Vermelho
    }

    # Painel principal
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock = [System.Windows.Forms.DockStyle]::Fill
    $panel.BackColor = $colors[$Type]
    $form.Controls.Add($panel)

    # Elementos gráficos
    $iconSize = 32
    $icon = if ($Type -eq "error") { 
        [System.Drawing.SystemIcons]::Error.ToBitmap() 
    } else { 
        [System.Drawing.SystemIcons]::Information.ToBitmap() 
    }

    $iconBox = New-Object System.Windows.Forms.PictureBox
    $iconBox.Size = New-Object System.Drawing.Size($iconSize, $iconSize)
    $iconBox.Location = New-Object System.Drawing.Point(10, ($formHeight - $iconSize)/2)
    $iconBox.Image = $icon
    $panel.Controls.Add($iconBox)

    # Textos
    $textX = $iconSize + 20
    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::White
    $lblTitle.Location = New-Object System.Drawing.Point($textX, 15)
    $lblTitle.Size = New-Object System.Drawing.Size(($formWidth - $textX - 10), 20)
    $lblTitle.Text = $Title
    $panel.Controls.Add($lblTitle)

    $lblMessage = New-Object System.Windows.Forms.Label
    $lblMessage.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $lblMessage.ForeColor = [System.Drawing.Color]::White
    $lblMessage.Location = New-Object System.Drawing.Point($textX, 35)
    $lblMessage.Size = New-Object System.Drawing.Size(($formWidth - $textX - 10), 40)
    $lblMessage.Text = $Message
    $panel.Controls.Add($lblMessage)

    # Temporizador
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 3000
    $timer.Add_Tick({ 
        $form.Close()
        $timer.Dispose()
    })
    $timer.Start()

    Write-Log -Message "$Title - $Message" -Level $Type
    $form.ShowDialog()
}

# VERIFICAÇÕES DO RCLONE
# ====================================================
function Test-RcloneConfig {
    try {
        Write-Log -Message "Verificando configuração do Rclone..." -Level Info
        
        # Verificar existência do executável
        if (-not (Test-Path $RclonePath)) {
            throw "Arquivo do Rclone não encontrado: $RclonePath"
        }

        # Verificar remote configurado
        $remotes = & $RclonePath listremotes 2>&1
        if (-not ($remotes -match "^${CloudRemote}:")) {
            throw "Remote '$CloudRemote' não configurado"
        }

        Write-Log -Message "Configuração do Rclone validada" -Level Info
    }
    catch {
        Write-Log -Message "ERRO: Falha na verificação do Rclone - $_" -Level Error
        Show-CustomNotification -Title "Erro de Configuração" -Message "Verifique as configurações do Rclone" -Type "error"
        exit 1
    }
}

# FUNÇÃO PRINCIPAL DO RCLONE
# ====================================================
function Invoke-RcloneCommand {
    param(
        [string]$Source,
        [string]$Destination
    )

    $maxRetries = 3
    $retryCount = 0
    $success = $false

    do {
        try {
            Write-Log -Message "Tentativa $($retryCount+1)/$maxRetries: $Source -> $Destination" -Level Info
            
            $arguments = @(
                "copy",
                "`"$Source`"",
                "`"$Destination`"",
                "--update",
                "--create-empty-src-dirs",
                "--stats=1s",
                "--log-level=DEBUG",
                "--retries=2",
                "--retries-sleep=5s"
            )

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

            if ($process.ExitCode -ne 0) {
                throw "Código de erro $($process.ExitCode)`nSaída: $($output + $errorOutput)"
            }

            $success = $true
            Write-Log -Message "Sincronização bem-sucedida" -Level Info
        }
        catch {
            $retryCount++
            Write-Log -Message "Falha na tentativa $retryCount: $_" -Level Warning
            Start-Sleep -Seconds 5
        }
    } while (-not $success -and $retryCount -lt $maxRetries)

    if (-not $success) {
        throw "Falha após $maxRetries tentativas: $Source -> $Destination"
    }
}

# FLUXO DE SINCRONIZAÇÃO
# ====================================================
function Sync-Saves {
    param([string]$Direction) # "up" ou "down"

    try {
        Show-CustomNotification -Title "Sincronização" -Message "Iniciando processo..." -Type "info"

        switch ($Direction) {
            "down" {
                Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir
            }
            "up" {
                Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/"
            }
        }

        Show-CustomNotification -Title "Sincronização" -Message "Concluído com sucesso!" -Type "success"
    }
    catch {
        Write-Log -Message "ERRO: Falha na sincronização - $_" -Level Error
        Show-CustomNotification -Title "Erro de Sincronização" -Message "Verifique o log" -Type "error"
        exit 1
    }
}

# EXECUÇÃO PRINCIPAL
# ====================================================
try {
    # Validação inicial
    Test-RcloneConfig

    # Criar diretório local
    if (-not (Test-Path -Path $LocalDir)) {
        try {
            New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
            Write-Log -Message "Diretório local criado: $LocalDir" -Level Info
        }
        catch {
            Write-Log -Message "Falha ao criar diretório: $_" -Level Error
            throw
        }
    }

    # Sincronização inicial (Download)
    Sync-Saves -Direction "down"

    # Iniciar jogo
    Show-CustomNotification -Title "Execução" -Message "Iniciando Elden Ring..." -Type "info"
    $gameProcess = Start-Process -FilePath $GameExePath -PassThru
    Write-Log -Message "Processo do jogo iniciado (PID: $($gameProcess.Id))" -Level Info

    # Monitorar execução
    Write-Log -Message "Monitorando processo do jogo..." -Level Info
    while ($null -ne (Get-Process -Name $GameProcess -ErrorAction SilentlyContinue)) {
        Start-Sleep -Seconds 5
    }

    # Sincronização final (Upload)
    Sync-Saves -Direction "up"
    Show-CustomNotification -Title "Conclusão" -Message "Processo finalizado!" -Type "success"
}
catch {
    Write-Log -Message "ERRO FATAL: $($_.Exception.Message)" -Level Error
    Write-Log -Message "Stack Trace: $($_.ScriptStackTrace)" -Level Error
    Show-CustomNotification -Title "Erro Crítico" -Message "Consulte o arquivo de log" -Type "error"
    exit 1
}
finally {
    Write-Log -Message "=== Sessão finalizada ===`n" -Level Info
}