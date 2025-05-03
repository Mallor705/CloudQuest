﻿# Sync-Save.ps1

# CONFIGURAÇÕES DO USUÁRIO
# ====================================================
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$LauncherExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$LogPath = Join-Path -Path $ScriptDir -ChildPath "Sync-Save.log"

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
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8 -Force
}

Set-Content -Path $LogPath -Value "=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===`n" -Encoding UTF8

# NOTIFICAÇÕES PERSONALIZADAS (ATUALIZADA)
# ====================================================
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info"
    )

    Write-Log -Message "$Title - $Message" -Level "Info"

    # Configurações de layout
    $formWidth = 300
    $formHeight = 100
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea

    # Criar formulário
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.Size = New-Object System.Drawing.Size($formWidth, $formHeight)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Location = New-Object System.Drawing.Point(
        [int]($screen.Width - $formWidth - 20),
        [int]($screen.Height - $formHeight - 20)
    )
    $form.TopMost = $true
    $form.BackColor = [System.Drawing.Color]::FromArgb(34, 39, 46)

    # Timer assíncrono para fechar após 3 segundos
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 3000
    $timer.Enabled = $true
    Register-ObjectEvent -InputObject $timer -EventName Tick -Action {
        $form.Close()
        $timer.Stop()
        $timer.Dispose()
    } | Out-Null

    # Painel principal
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock = [System.Windows.Forms.DockStyle]::Fill
    $panel.BackColor = $form.BackColor
    $form.Controls.Add($panel)

    # Ícone
    $iconSize = 24
    $icon = if ($Type -eq "error") {
        [System.Drawing.SystemIcons]::Error.ToBitmap()
    } else {
        [System.Drawing.SystemIcons]::Information.ToBitmap()
    }

    $iconBox = New-Object System.Windows.Forms.PictureBox
    $iconBox.Size = New-Object System.Drawing.Size($iconSize, $iconSize)
    $iconBox.Location = New-Object System.Drawing.Point(10, [int](($formHeight - $iconSize) / 2))
    $iconBox.Image = $icon
    $panel.Controls.Add($iconBox)

    # Textos
    $textX = $iconSize + 20
    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::White
    $lblTitle.Location = New-Object System.Drawing.Point($textX, 10)
    $lblTitle.Size = New-Object System.Drawing.Size([int]($formWidth - $textX - 10), 20)
    $lblTitle.Text = $Title
    $panel.Controls.Add($lblTitle)

    $lblMessage = New-Object System.Windows.Forms.Label
    $lblMessage.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $lblMessage.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 200)
    $lblMessage.Location = New-Object System.Drawing.Point($textX, 30)
    $lblMessage.Size = New-Object System.Drawing.Size([int]($formWidth - $textX - 10), 30)
    $lblMessage.Text = $Message
    $panel.Controls.Add($lblMessage)

    $form.Add_Shown({ $form.Activate() })
    $form.ShowInTaskbar = $false
    $form.Show()

    return @{ Form = $form; Timer = $timer }
}

# VERIFICAÇÕES DO RCLONE
# ====================================================
function Test-RcloneConfig {
    try {
        Write-Log -Message "Verificando configuração do Rclone..." -Level Info
        
        if (-not (Test-Path $RclonePath)) {
            throw "Arquivo do Rclone não encontrado: $RclonePath"
        }

        $remotes = & $RclonePath listremotes 2>&1
        if ($remotes -is [System.Management.Automation.ErrorRecord]) {
            throw $remotes.Exception.Message
        }
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

# FUNÇÃO PRINCIPAL DO RCLONE (ATUALIZADA)
# ====================================================
function Invoke-RcloneCommand {
    param(
        [string]$Source,
        [string]$Destination,
        [hashtable]$Notification
    )

    $maxRetries = 3
    $retryCount = 0
    $success = $false
    $startTime = Get-Date

    do {
        try {
            Write-Log -Message "Tentativa $($retryCount+1)/${maxRetries}: $Source -> $Destination" -Level Info
            
            $arguments = @(
                "copy",
                "`"$Source`"",
                "`"$Destination`"",
                "--update",
                "--create-empty-src-dirs"
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

            $completed = $process.WaitForExit(30000)

            if (-not $completed) {
                $process.Kill()
                throw "Timeout: Rclone excedeu 30 segundos."
            }

            $output = $process.StandardOutput.ReadToEnd()
            $errorOutput = $process.StandardError.ReadToEnd()

            if ($process.ExitCode -ne 0) {
                throw "Código de erro $($process.ExitCode)`nSaída: $($output + $errorOutput)"
            }

            $success = $true
            Write-Log -Message "Sincronização bem-sucedida" -Level Info
        }
        catch {
            $retryCount++
            Write-Log -Message "Falha na tentativa ${retryCount}: $_" -Level Warning
            Start-Sleep -Seconds 5
        }
    } while (-not $success -and $retryCount -lt $maxRetries)

    # Fechar notificação se já passaram 3 segundos
    $elapsed = (Get-Date) - $startTime
    if ($elapsed.TotalMilliseconds -lt 3000) {
        Start-Sleep -Milliseconds (3000 - $elapsed.TotalMilliseconds)
    }
    $Notification.Form.Close()
    $Notification.Timer.Stop()

    if (-not $success) {
        throw "Falha após $maxRetries tentativas: $Source -> $Destination"
    }
}

# FLUXO DE SINCRONIZAÇÃO (ATUALIZADO)
# ====================================================
function Sync-Saves {
    param([string]$Direction)

    $notification = $null
    try {
        switch ($Direction) {
            "down" {
                $notification = Show-CustomNotification -Title "Steam Cloud" -Message "Sincronizando com Nuvem" -Type "sync"
                Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir -Notification $notification
            }
            "up" {
                $notification = Show-CustomNotification -Title "Steam Cloud" -Message "Atualizando Nuvem" -Type "update"
                Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/" -Notification $notification
            }
        }
    }
    catch {
        if ($null -ne $notification) { 
            $notification.Timer.Stop()
            $notification.Form.Close()
        }
        Write-Log -Message "ERRO: Falha na sincronização - $_" -Level Error
        Show-CustomNotification -Title "Erro" -Message "Falha na sincronização" -Type "error"
        exit 1
    }
}

# EXECUÇÃO PRINCIPAL (ATUALIZADA)
# ====================================================
try {
    Test-RcloneConfig

    try {
        & $RclonePath mkdir "$($CloudRemote):$($CloudDir)"
        Write-Log -Message "Diretório remoto verificado/criado: $($CloudRemote):$($CloudDir)" -Level Info
    }
    catch {
        Write-Log -Message "Falha ao criar diretório remoto: $_" -Level Error
        throw
    }

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

    Sync-Saves -Direction "down"

    # Iniciar Launcher
    $launcherProcess = Start-Process -FilePath $LauncherExePath -WindowStyle Hidden -PassThru
    Write-Log -Message "Launcher iniciado (PID: $($launcherProcess.Id))" -Level Info

    # Aguardar processo do jogo
    Write-Log -Message "Aguardando processo do jogo..." -Level Info
    $timeout = 10
    $startTime = Get-Date
    $validatedGameProcess = $GameProcess
    $gameProcess = $null

    while (-not $gameProcess -and ((Get-Date) - $startTime).TotalSeconds -lt $timeout) {
        try {
            $gameProcess = Get-Process -Name $validatedGameProcess -ErrorAction SilentlyContinue
        } catch {
            Write-Log -Message "Erro ao buscar o processo '$validatedGameProcess': $_" -Level Warning
        }
        Start-Sleep -Seconds 5
    }

    if (-not $gameProcess) {
        throw "Processo do jogo não iniciado após $timeout segundos"
    }

    # Monitorar jogo (NÃO BLOQUEANTE)
    try {
        Write-Log -Message "Iniciando monitoramento do processo (PID: $($gameProcess.Id))..." -Level Info
        
        while (-not $gameProcess.HasExited) {
            Start-Sleep -Milliseconds 500
            [System.Windows.Forms.Application]::DoEvents() # Manter UI responsiva
        }

        Write-Log -Message "Processo finalizado (PID: $($gameProcess.Id))" -Level Info
    }
    catch {
        Write-Log -Message "Erro ao monitorar o processo: $_" -Level Error
        throw "Falha no monitoramento"
    }

    Sync-Saves -Direction "up"
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