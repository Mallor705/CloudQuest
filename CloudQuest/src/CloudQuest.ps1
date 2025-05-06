# CloudQuest.ps1
# INICIALIZAÇÃO DO SISTEMA
# ====================================================

$runspace = [runspacefactory]::CreateRunspace()
$runspace.Open()
[runspacefactory]::DefaultRunspace = $runspace

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing


# Importa módulos necessários
try {
    Import-Module (Join-Path $PSScriptRoot "modules\Rclone.psm1") -ErrorAction Stop
    Import-Module (Join-Path $PSScriptRoot "modules\Config.psm1") -ErrorAction Stop
    Import-Module (Join-Path $PSScriptRoot "modules\Notifications.psm1") -ErrorAction Stop
}
catch {
    Write-Host "ERRO FATAL: Não foi possível carregar os módulos necessários: $_"
    exit 1
}


# FLUXO DE SINCRONIZAÇÃO (CORRIGIDO)
function Sync-Saves {
    param([string]$Direction)

    $notification = $null
    try {
        switch ($Direction) {
            "down" {
                # Tratamento para possíveis erros na notificação
                try {
                    $notification = Show-CustomNotification -Title "CloudQuest" -Message "Sincronizando" -Direction "sync"
                    if ($null -eq $notification) { 
                        Write-Log -Message "Aviso: Notificação não foi criada" -Level Warning
                    }
                }
                catch {
                    Write-Log -Message "Erro ao criar notificação: $_" -Level Error
                }
                
                # Continua com a sincronização mesmo se a notificação falhar
                Invoke-RcloneCommand -Source "$($CloudRemote):$($CloudDir)/" -Destination $LocalDir -Notification $notification
            }
            "up" {
                try {
                    $notification = Show-CustomNotification -Title "CloudQuest" -Message "Atualizando" -Direction "update"
                    if ($null -eq $notification) { 
                        Write-Log -Message "Aviso: Notificação não foi criada" -Level Warning
                    }
                }
                catch {
                    Write-Log -Message "Erro ao criar notificação: $_" -Level Error
                }
                
                Invoke-RcloneCommand -Source $LocalDir -Destination "$($CloudRemote):$($CloudDir)/" -Notification $notification
            }
        }
    }
    catch {
        # Tratamento seguro da notificação em caso de erro
        try {
            if ($null -ne $notification) { 
                if ($notification.ContainsKey('Timer') -and $null -ne $notification.Timer) { 
                    $notification.Timer.Stop() 
                }
                if ($notification.ContainsKey('Form') -and $null -ne $notification.Form -and -not $notification.Form.IsDisposed) { 
                    $notification.Form.Close() 
                }
            }
        }
        catch {
            Write-Log -Message "Erro ao fechar notificação: $_" -Level Error
        }
        
        Write-Log -Message "ERRO: Falha na sincronização - $_" -Level Error
        
        # Tratamento seguro da notificação de erro
        try {
            Show-CustomNotification -Title "Erro" -Message "Falha na sincronização" -Type "error" | Out-Null
        }
        catch {
            Write-Log -Message "Falha ao exibir notificação de erro: $_" -Level Error
        }
    }
}

# EXECUÇÃO PRINCIPAL
try {
    # Verificação do Rclone (não crítico)
    try {
        Test-RcloneConfig
    }
    catch {
        Write-Log -Message "AVISO: Verificação do Rclone falhou. Continuando com execução..." -Level Warning
    }
    
    # Criar diretório remoto (não crítico)
    try {
        & $RclonePath mkdir "$($CloudRemote):$($CloudDir)"
        Write-Log -Message "Diretório remoto verificado/criado: $($CloudRemote):$($CloudDir)" -Level Info
    }
    catch {
        Write-Log -Message "AVISO: Falha ao criar diretório remoto. Continuando..." -Level Error
    }

    # Criar diretório local (crítico?)
    if (-not (Test-Path -Path $LocalDir)) {
        try {
            New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
            Write-Log -Message "Diretório local criado: $LocalDir" -Level Info
        }
        catch {
            Write-Log -Message "ERRO: Falha ao criar diretório local. O jogo pode não funcionar corretamente." -Level Error
            # Não interrompe; o jogo pode criar o diretório
        }
    }

    # Download da nuvem para local
    Sync-Saves -Direction "down"

    # Iniciar Launcher (crítico)
    $launcherProcess = $null
    try {
        if (-not (Test-Path -Path $LauncherExePath)) {
            throw "Caminho do launcher não encontrado: $LauncherExePath"
        }
        
        $launcherProcess = Start-Process -FilePath $LauncherExePath -WindowStyle Hidden -PassThru
        if ($null -eq $launcherProcess) {
            throw "Falha ao iniciar launcher"
        }
        
        Write-Log -Message "Launcher iniciado (PID: $($launcherProcess.Id))" -Level Info
    }
    catch {
        Write-Log -Message "ERRO FATAL: Não foi possível iniciar o launcher: $_" -Level Error
        # Tentar exibir uma notificação de erro final antes de encerrar
        try {
            Show-CustomNotification -Title "Erro Crítico" -Message "Falha ao iniciar o jogo" -Type "error" | Out-Null
        }
        catch {}
        throw # Interrompe o script, pois sem o launcher, não há jogo.
    }
    
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
        
        # Usar WaitForExit com timeout curto em vez de loop infinito
        while (-not $gameProcess.HasExited) {
            Start-Sleep -Milliseconds 500
            try {
                # Manter UI responsiva sem usar DoEvents que pode causar problemas
                [System.Windows.Forms.Application]::DoEvents()
                
                # Verificar periodicamente se o processo ainda existe
                if ($null -eq (Get-Process -Id $gameProcess.Id -ErrorAction SilentlyContinue)) {
                    break
                }
            }
            catch {
                Write-Log -Message "Erro ao verificar processo: $_" -Level Warning
                break
            }
        }

        Write-Log -Message "Processo finalizado (PID: $($gameProcess.Id))" -Level Info
    }
    catch {
        Write-Log -Message "Erro ao monitorar o processo: $_" -Level Error
        # Continuar para sincronizar mesmo se o monitoramento falhar
    }

    # Upload do local para a nuvem
    Sync-Saves -Direction "up"
}
catch {
    Write-Log -Message "ERRO FATAL: $($_.Exception.Message)" -Level Error
    Write-Log -Message "Stack Trace: $($_.ScriptStackTrace)" -Level Error
    
    # Tratamento seguro da notificação final de erro
    try {
        Show-CustomNotification -Title "Erro Crítico" -Message "Consulte o arquivo de log" -Type "error" | Out-Null
    }
    catch {
        Write-Log -Message "Não foi possível mostrar notificação final: $_" -Level Error
    }
    exit 1
}
finally {
    Write-Log -Message "=== Sessão finalizada ===`n" -Level Info
}