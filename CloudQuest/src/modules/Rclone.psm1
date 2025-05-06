# VERIFICAÇÕES DO RCLONE
# ====================================================
function Test-RcloneConfig {
    try {
        Write-Log -Message "Verificando configuração do Rclone..." -Level Info
        
        if (-not (Test-Path $global:RclonePath)) {
            throw "Arquivo do Rclone não encontrado: $global:RclonePath"
        }
        
        $remotes = & $global:RclonePath listremotes 2>&1
        if ($remotes -is [System.Management.Automation.ErrorRecord]) {
            throw $remotes.Exception.Message
        }
        if (-not ($remotes -match "^$($global:CloudRemote):")) {
            throw "Remote '$global:CloudRemote' não configurado"
        }
        
        Write-Log -Message "Configuração do Rclone validada" -Level Info
    }
    catch {
        Write-Log -Message "ERRO: Falha na verificação do Rclone - $_" -Level Error
        
        # Tratamento seguro da notificação de erro
        try {
            Show-CustomNotification -Title "Erro de Configuração" -Message "Verifique as configurações do Rclone" -Type "error" | Out-Null
        }
        catch {
            Write-Log -Message "Falha ao exibir notificação de erro do Rclone: $_" -Level Error
        }
        throw $_
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
            
            # Aguarda com timeout para evitar bloqueio indefinido
            $completed = $process.WaitForExit(120000)  # 2 minutos de timeout
            
            if (-not $completed) {
                $process.Kill()
                throw "Timeout: Rclone excedeu 2 minutos."
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

    # Fechar notificação de forma segura
    try {
        # Fechar notificação se já passaram 5 segundos
        $elapsed = (Get-Date) - $startTime
        $remaining = [int](5000 - $elapsed.TotalMilliseconds)
        
        if ($remaining -gt 0) {
            Start-Sleep -Milliseconds $remaining
        }

        if ($Notification -and 
            $Notification.ContainsKey('Form') -and $null -ne $Notification.Form -and -not $Notification.Form.IsDisposed) {
            $Notification.Form.Close()
        }
    }
    catch {
        Write-Log -Message "Erro ao fechar notificação: $_" -Level Warning
    }

    if (-not $success) {
        throw "Falha após $maxRetries tentativas: $Source -> $Destination"
    }
}

# Exporta as funções para uso em outros módulos
Export-ModuleMember -Function Test-RcloneConfig, Invoke-RcloneCommand