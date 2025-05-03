# Sync-Save.ps1

# CONFIGURAÇÕES DO USUÁRIO
# ====================================================
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"         # Processo REAL do jogo
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

# NOTIFICAÇÕES PERSONALIZADAS (ESTILO STEAM)
# ====================================================
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info" # Tipos: "sync", "update", "error"
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

    # Retornar o formulário para controle externo
    $form.Add_Shown({ $form.Activate() })
    $form.ShowInTaskbar = $false
    
    # Exibir e retornar o objeto
    $form.Show()
    return $form
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

# FUNÇÃO PRINCIPAL DO RCLONE (MODIFICADA)
# ====================================================
function Invoke-RcloneCommand {
    param(
        [string]$Source,
        [string]$Destination,
        [System.Windows.Forms.Form]$NotificationForm
    )

    $maxRetries = 3
    $retryCount = 0
    $success = $false

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

            # Configurar timeout (30 segundos)
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

            # Timeout de 30 segundos para operação
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
            # Fechar notificação ao finalizar
            if ($success) {
                $NotificationForm.Close()
            }
        }
        catch {
            $retryCount++
            Write-Log -Message "Falha na tentativa ${retryCount}: $_" -Level Warning
            Start-Sleep -Seconds 5
        }
    } while (-not $success -and $retryCount -lt $maxRetries)

    # Fechar notificação mesmo em caso de falha
    $NotificationForm.Close()

    if (-not $success) {
        throw "Falha após $maxRetries tentativas: $Source -> $Destination"
    }
}

# FLUXO DE SINCRONIZAÇÃO ATUALIZADO
# ====================================================
function Sync-Saves {
    param([string]$Direction)

    $notification = $null
    try {
        switch ($Direction) {
            "down" {
                $notification = Show-CustomNotification -Title "Steam Cloud" -Message "Sincronizando com Nuvem" -Type "sync"
                Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir -NotificationForm $notification
            }
            "up" {
                $notification = Show-CustomNotification -Title "Steam Cloud" -Message "Atualizando Nuvem" -Type "update"
                Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/" -NotificationForm $notification
            }
        }
    }
    catch {
        if ($null -ne $notification) { $notification.Close() }
        Write-Log -Message "ERRO: Falha na sincronização - $_" -Level Error
        Show-CustomNotification -Title "Erro" -Message "Falha na sincronização" -Type "error"
        exit 1
    }
}

# EXECUÇÃO PRINCIPAL
# ====================================================
try {
    Test-RcloneConfig

    try {
        Write-Log -Message "Criando diretório remoto (se não existir)..." -Level Info
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
    # Show-CustomNotification -Title "Execução" -Message "Iniciando Elden Ring..." -Type "info"
    $launcherProcess = Start-Process -FilePath $LauncherExePath -WindowStyle Hidden -PassThru
    Write-Log -Message "Launcher iniciado (PID: $($launcherProcess.Id))" -Level Info

    # Aguardar processo do jogo
    Write-Log -Message "Aguardando processo do jogo..." -Level Info
    $timeout = 10
    $startTime = Get-Date

    if (-not $GameProcess -or [string]::IsNullOrWhiteSpace($GameProcess)) {
        Write-Log -Message "O parâmetro 'GameProcess' está vazio ou nulo. Verifique as configurações do script." -Level Error
        throw "O parâmetro 'GameProcess' não foi configurado ou está vazio. Verifique as configurações do script."
    }
    Write-Log -Message "Parâmetro 'GameProcess' validado: $GameProcess" -Level Info

    # Garantir que o valor de $GameProcess não seja alterado
    $validatedGameProcess = $GameProcess
    Write-Log -Message "Usando o valor de 'GameProcess': $validatedGameProcess" -Level Info

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

    # Após detectar o processo do jogo:
    Write-Log -Message "Processo do jogo detectado (PID: $($gameProcess.Id))" -Level Info

# Monitorar jogo
try {
    Write-Log -Message "Iniciando monitoramento do processo (PID: $($gameProcess.Id))..." -Level Info
    
    # Usar Wait-Process (não requer admin)
    $gameProcess | Wait-Process -ErrorAction Stop
    
    Write-Log -Message "Processo finalizado (PID: $($gameProcess.Id))" -Level Info
}
catch {
    Write-Log -Message "Erro ao monitorar o processo: $_" -Level Error
    throw "Falha no monitoramento"
}
    # Sincronizar APÓS o processo ser fechado
    # Start-Sleep -Seconds 5  # Pausa de 5 segundos
    Sync-Saves -Direction "up"
    # Show-CustomNotification -Title "Conclusão" -Message "Processo finalizado!" -Type "success"
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