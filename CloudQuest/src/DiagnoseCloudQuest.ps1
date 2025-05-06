function Test-CloudQuestDiagnostic {
    param(
        [string]$ProfileName
    )
    
    # Detectar caminhos
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProfilesDir = Join-Path -Path $ScriptDir -ChildPath "profiles"
    
    Write-Host "=== CloudQuest Diagnostic Tool ==="
    Write-Host "Diretório atual: $ScriptDir"
    Write-Host "Diretório de perfis: $ProfilesDir"
    
    # Verificar se o diretório de perfis existe
    if (-not (Test-Path -Path $ProfilesDir)) {
        Write-Host "ERRO: Diretório de perfis não encontrado!" -ForegroundColor Red
        return
    }
    
    # Listar perfis disponíveis
    $profiles = Get-ChildItem -Path $ProfilesDir -Filter "*.json" | ForEach-Object { $_.BaseName }
    Write-Host "Perfis encontrados: $($profiles.Count)"
    foreach ($p in $profiles) {
        Write-Host "- $p"
    }
    
    # Se nenhum perfil foi especificado, perguntar ao usuário
    if ([string]::IsNullOrEmpty($ProfileName)) {
        if ($profiles.Count -eq 0) {
            Write-Host "Nenhum perfil encontrado para testar." -ForegroundColor Red
            return
        }
        Write-Host "`nSelecione um perfil para diagnosticar:"
        for ($i = 0; $i -lt $profiles.Count; $i++) {
            Write-Host "[$i] $($profiles[$i])"
        }
        $selection = Read-Host "Digite o número"
        if ([int]::TryParse($selection, [ref]$null)) {
            $ProfileName = $profiles[[int]$selection]
        } else {
            Write-Host "Seleção inválida." -ForegroundColor Red
            return
        }
    }
    
    # Carregar perfil
    $profileFile = Join-Path -Path $ProfilesDir -ChildPath "$ProfileName.json"
    if (-not (Test-Path -Path $profileFile)) {
        Write-Host "ERRO: Perfil '$ProfileName' não encontrado!" -ForegroundColor Red
        return
    }
    
    Write-Host "`nTestando perfil: $ProfileName"
    try {
        $config = Get-Content -Path $profileFile -Raw | ConvertFrom-Json
        
        # Verificar campos obrigatórios
        $requiredFields = @("RclonePath", "CloudRemote", "CloudDir", "LocalDir", "GameProcess", "GameName", "ExecutablePath")
        $hasErrors = $false
        
        foreach ($field in $requiredFields) {
            $value = $config.$field
            if ([string]::IsNullOrEmpty($value)) {
                Write-Host "ERRO: Campo '$field' está vazio ou ausente!" -ForegroundColor Red
                $hasErrors = $true
            } else {
                Write-Host "$field = $value"
                
                # Verificações adicionais para certos campos
                if ($field -eq "RclonePath" -and -not (Test-Path -Path $value)) {
                    Write-Host "  ERRO: Arquivo Rclone não encontrado!" -ForegroundColor Red
                    $hasErrors = $true
                }
                if ($field -eq "ExecutablePath" -and -not (Test-Path -Path $value)) {
                    Write-Host "  AVISO: Executável do jogo não encontrado!" -ForegroundColor Yellow
                }
                if ($field -eq "LocalDir" -and -not (Test-Path -Path $value)) {
                    Write-Host "  AVISO: Diretório local não existe (será criado automaticamente)" -ForegroundColor Yellow
                }
            }
        }
        
        # Testar conexão Rclone
        if (Test-Path -Path $config.RclonePath) {
            Write-Host "`nTestando execução do Rclone..."
            $rcloneVersion = & $config.RclonePath version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Rclone executado com sucesso!" -ForegroundColor Green
                Write-Host $rcloneVersion
                
                # Testar remote
                Write-Host "`nListando remotes configurados..."
                $remotes = & $config.RclonePath listremotes 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Remotes disponíveis:"
                    foreach ($remote in $remotes) {
                        Write-Host "- $remote"
                    }
                    
                    # Verificar se o remote especificado existe
                    $remoteExists = $remotes -match "^$($config.CloudRemote):"
                    if ($remoteExists) {
                        Write-Host "Remote '$($config.CloudRemote)' encontrado!" -ForegroundColor Green
                    } else {
                        Write-Host "ERRO: Remote '$($config.CloudRemote)' não encontrado!" -ForegroundColor Red
                        $hasErrors = $true
                    }
                } else {
                    Write-Host "ERRO ao listar remotes: $remotes" -ForegroundColor Red
                    $hasErrors = $true
                }
            } else {
                Write-Host "ERRO ao executar Rclone: $rcloneVersion" -ForegroundColor Red
                $hasErrors = $true
            }
        }
        
        # Resumo
        Write-Host "`n=== Resumo do Diagnóstico ==="
        if ($hasErrors) {
            Write-Host "Foram encontrados problemas que precisam ser corrigidos!" -ForegroundColor Red
        } else {
            Write-Host "Nenhum problema crítico encontrado. O perfil parece estar correto." -ForegroundColor Green
        }
        
    } catch {
        Write-Host "ERRO ao processar o perfil: $_" -ForegroundColor Red
    }
}

# Executar diagnóstico
Test-CloudQuestDiagnostic