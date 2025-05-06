# CloudQuest.ps1
# INICIALIZAÇÃO DO SISTEMA
# ====================================================

$runspace = [runspacefactory]::CreateRunspace()
$runspace.Open()
[runspacefactory]::DefaultRunspace = $runspace

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing


# Importa módulos necessários
Import-Module (Join-Path $PSScriptRoot "modules\Config.psm1")
Import-Module (Join-Path $PSScriptRoot "modules\Notifications.psm1")
Import-Module (Join-Path $PSScriptRoot "modules\Rclone.psm1")


# FLUXO DE SINCRONIZAÇÃO (ATUALIZADO)
function Sync-Saves {
    param([string]$Direction)

    $notification = $null
    try {
        switch ($Direction) {
            "down" {
                $notification = Show-CustomNotification -Title "CloudQuest" -Message "Sincronizando" -Direction "sync"
                Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir -Notification $notification
            }
            "up" {
                $notification = Show-CustomNotification -Title "CloudQuest" -Message "Atualizando" -Direction "update"
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
        # exit 1
    }
}

# EXECUÇÃO PRINCIPAL
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
    $timeout = 60
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

# As chamadas a Test-RcloneConfig, Invoke-RcloneCommand e Show-CustomNotification estão integradas corretamente.