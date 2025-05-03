# ER_Sync.ps1
# Versão Final: Sincronização + Log + Notificações Personalizadas Corrigidas

# CONFIGURAÇÕES DO USUÁRIO
# ---------------------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------------------
"`n=== [ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ] Sessão iniciada ===" | Out-File -FilePath $LogPath -Append

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    $logEntry | Out-File -FilePath $LogPath -Append -Encoding UTF8  # Corrige encoding
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

    # Cálculo corrigido da posição
    $screenWidth = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Width
    $screenHeight = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea.Height

    # Criar formulário
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.Size = New-Object System.Drawing.Size(350, 80)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.Location = New-Object System.Drawing.Point(
        ($screenWidth - 370),  # Posição X corrigida
        ($screenHeight - 90)   # Posição Y corrigida
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

# FUNÇÕES DE SINCRONIZAÇÃO
# ---------------------------------------------------------------------------------------
function Invoke-RcloneCommand {
    param($Source, $Destination)

    $arguments = @(
        "copy",
        "`"$Source`"",
        "`"$Destination`"",
        "--update",
        "--create-empty-src-dirs",
        "--stats=1s",
        "--log-level=NOTICE",  # Nível mais detalhado
        "--retries=3",         # Tentativas de repetição
        "--retries-sleep=5s"   # Intervalo entre tentativas
    )

    Write-Log -Message "Executando: rclone $($arguments -join ' ')" -Level Info
    $startTime = Get-Date

    try {
        $output = & $RclonePath $arguments 2>&1  # Captura todos os fluxos
        
        if ($LASTEXITCODE -ne 0) {
            throw "Erro Rclone (Código $LASTEXITCODE)"
        }
        
        Write-Log -Message "Comando executado com sucesso" -Level Info
        Write-Log -Message "Saída detalhada:`n$output" -Level Info
    }
    catch {
        Write-Log -Message "FALHA NA SINCRONIZAÇÃO - Detalhes:`n$output" -Level Error
        throw $_.Exception
    }
    finally {
        $duration = (Get-Date) - $startTime
        Write-Log -Message "Duração da operação: $($duration.ToString('mm\:ss'))" -Level Info
    }
}

# VERIFICAÇÃO DO REMOTE RCLONE
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


function Sync-Saves {
    try {
        Show-CustomNotification -Title "Sincronização" -Message "Iniciando sincronização de saves..." -Type "info"
        
        # Fase de download
        Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir
        
        # Fase de upload
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
    # Verificação de diretório
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
    Show-CustomNotification -Title "Erro Fatal" -Message "Ocorreu um erro crítico" -Type "error"
}
finally {
    Write-Log -Message "=== Sessão finalizada ===`n" -Level Info
}