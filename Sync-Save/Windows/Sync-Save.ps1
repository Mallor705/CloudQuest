# ER_Sync.ps1
# Versão 6.0 - Codificação UTF-8, Verificação de Configuração e Tratamento Aprimorado

# CONFIGURAÇÕES DO USUÁRIO
# =======================================================================================
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"
$CloudRemote = "onedrive"
$CloudDir = "SaveGames/EldenRing"
$LocalDir = "$env:APPDATA\EldenRing"
$GameProcess = "eldenring"
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"
$LogPath = "$env:APPDATA\Sync-Save.log"

# INICIALIZAÇÃO DO SISTEMA
# =======================================================================================
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# CONFIGURAÇÃO DO LOG (UTF-8)
# =======================================================================================
"`n=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===" | Out-File -FilePath $LogPath -Append -Encoding UTF8

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

# NOTIFICAÇÕES PERSONALIZADAS
# =======================================================================================
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info"  # info, success, error
    )

    # Configuração de cores
    $colors = @{
        "info"    = [System.Drawing.Color]::FromArgb(45,125,255)
        "success" = [System.Drawing.Color]::FromArgb(40,167,69)
        "error"   = [System.Drawing.Color]::FromArgb(220,53,69)
    }

    # Cálculo de posição corrigido
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $formWidth = 350
    $formHeight = 80

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

    # Painel principal
    $panel = New-Object System.Windows.Forms.Panel
    $panel.Dock = [System.Windows.Forms.DockStyle]::Fill
    $panel.BackColor = $colors[$Type]
    $form.Controls.Add($panel)

    # Ícone dinâmico
    $iconBox = New-Object System.Windows.Forms.PictureBox
    $iconBox.Size = New-Object System.Drawing.Size(32, 32)
    $iconBox.Location = New-Object System.Drawing.Point(15, 20)
    $iconBox.Image = if ($Type -eq "error") { 
        [System.Drawing.SystemIcons]::Error.ToBitmap() 
    } else { 
        [System.Drawing.SystemIcons]::Information.ToBitmap() 
    }
    $panel.Controls.Add($iconBox)

    # Elementos de texto
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

    # Temporizador de fechamento
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

# FUNÇÕES DO RCLONE
# =======================================================================================
function Test-RcloneConfig {
    try {
        Write-Log -Message "Verificando configuração do remote '$CloudRemote'" -Level Info
        $check = & $RclonePath listremotes
        if (-not ($check -match "^${CloudRemote}:$")) {
            throw "Remote '$CloudRemote' não configurado"
        }
        Write-Log -Message "Remote validado com sucesso" -Level Info
    }
    catch {
        Write-Log -Message "ERRO DE CONFIGURAÇÃO: $_" -Level Error
        throw
    }
}

function Invoke-RcloneCommand {
    param($Source, $Destination)

    $arguments = @(
        "copy",
        "`"$Source`"",
        "`"$Destination`"",
        "--update",
        "--create-empty-src-dirs",
        "--stats=1s",
        "--log-level=NOTICE",
        "--retries=3",
        "--retries-sleep=5s"
    )

    $startTime = Get-Date
    Write-Log -Message "Executando: rclone $($arguments -join ' ')" -Level Info

    try {
        $output = & $RclonePath $arguments 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            throw "Erro Rclone (Código $LASTEXITCODE)"
        }
        
        Write-Log -Message "Saída detalhada:`n$($output -join "`n")" -Level Info
        return $true
    }
    catch {
        Write-Log -Message "FALHA NA SINCRONIZAÇÃO - Detalhes:`n$($output -join "`n")" -Level Error
        throw $_.Exception
    }
    finally {
        $duration = (Get-Date) - $startTime
        Write-Log -Message "Duração da operação: $($duration.ToString('mm\:ss'))" -Level Info
    }
}

# FUNÇÃO DE SINCRONIZAÇÃO
# =======================================================================================
function Sync-Saves {
    try {
        Show-CustomNotification -Title "Sincronização" -Message "Iniciando sincronização de saves..." -Type "info"
        
        # Fase de download
        if (-not (Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir)) {
            throw "Falha na sincronização (Download)"
        }
        
        # Fase de upload
        if (-not (Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/")) {
            throw "Falha na sincronização (Upload)"
        }
        
        Show-CustomNotification -Title "Sincronização" -Message "Sincronização concluída!" -Type "success"
    }
    catch {
        Show-CustomNotification -Title "Erro de Sincronização" -Message "Falha durante a sincronização" -Type "error"
        exit 1
    }
}

# EXECUÇÃO PRINCIPAL
# =======================================================================================
try {
    # Verificação inicial
    Test-RcloneConfig

    # Criar diretório se necessário
    if (-not (Test-Path -Path $LocalDir)) {
        try {
            New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
            Show-CustomNotification -Title "Configuração" -Message "Diretório local criado" -Type "success"
            Write-Log -Message "Diretório local criado com sucesso" -Level Info
        }
        catch {
            Show-CustomNotification -Title "Erro Crítico" -Message "Falha ao criar diretório" -Type "error"
            Write-Log -Message "Falha ao criar diretório: $_" -Level Error
            exit 1
        }
    }

    # Sincronização inicial
    Sync-Saves

    # Inicialização do jogo
    Show-CustomNotification -Title "Execução" -Message "Iniciando Elden Ring..." -Type "info"
    $gameProcess = Start-Process -FilePath $GameExePath -PassThru
    Write-Log -Message "Processo do jogo iniciado (PID: $($gameProcess.Id))" -Level Info

    # Monitoramento
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
    Write-Log -Message "Stack Trace: $($_.ScriptStackTrace)" -Level Error
    Show-CustomNotification -Title "Erro Fatal" -Message "Operação interrompida" -Type "error"
    exit 1
}
finally {
    Write-Log -Message "=== Sessão finalizada ===`n" -Level Info
}