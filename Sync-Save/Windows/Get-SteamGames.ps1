# Requer PowerShell versão 5 ou superior
# Necessário conexão com internet para obter nomes precisos dos jogos

# Configurar política de execução (executar como Admin se necessário)
# Set-ExecutionPolicy RemoteSigned -Scope Process -Force

$steamPath = Get-ItemProperty -Path "HKCU:\Software\Valve\Steam" -Name "SteamPath" | Select-Object -ExpandProperty "SteamPath"
$libraryFolders = @($steamPath.Replace('/', '\'))

# Analisar libraryfolders.vdf para encontrar bibliotecas adicionais
$vdfPath = Join-Path $steamPath "steamapps\libraryfolders.vdf"
if (Test-Path $vdfPath) {
    $vdfContent = Get-Content -Path $vdfPath -Raw
    $pathMatches = [regex]::Matches($vdfContent, '"path"\s+"([^"]+)"')
    
    foreach ($match in $pathMatches) {
        $cleanPath = $match.Groups[1].Value.Replace('\\\\', '\').Trim()
        $libraryFolders += $cleanPath
    }
}

$gamesList = [System.Collections.Generic.List[PSObject]]::new()

foreach ($library in $libraryFolders) {
    # Normalizar caminho e validar
    $library = $library.TrimEnd('\') + '\'
    
    if (-not (Test-Path -LiteralPath $library)) {
        Write-Warning "[SKIPPED] Biblioteca não encontrada: $library"
        continue
    }

    $appsPath = Join-Path -Path $library -ChildPath "steamapps"
    
    if (-not (Test-Path $appsPath)) {
        Write-Warning "[SKIPPED] Pasta steamapps não existe em: $library"
        continue
    }

    # Procurar manifestos de aplicativos
    $manifests = Get-ChildItem -Path "$appsPath\appmanifest_*.acf" -ErrorAction SilentlyContinue
    
    foreach ($manifest in $manifests) {
        try {
            $content = Get-Content $manifest.FullName -Raw
            
            $appID = [regex]::Match($content, '"appid"\s+"(\d+)"').Groups[1].Value
            $installDir = [regex]::Match($content, '"installdir"\s+"([^"]+)"').Groups[1].Value
            $gamePath = Join-Path "$appsPath\common" $installDir

            if (-not (Test-Path $gamePath)) {
                Write-Warning "[MISSING] Pasta do jogo não encontrada: $gamePath"
                continue
            }

            # Buscar nome na API Steam
            $gameName = $null
            try {
                $apiUrl = "https://store.steampowered.com/api/appdetails?appids=$appID"
                $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
                $gameName = $response.$appID.data.name
            } catch {
                $gameName = "Nome não disponível (API offline)"
            }

            # Encontrar executáveis
            $exes = @(Get-ChildItem -Path $gamePath -Filter *.exe -Recurse -File | Select-Object -ExpandProperty Name)

            $gamesList.Add([PSCustomObject]@{
                AppID       = $appID
                NomeReal    = if ($gameName) { $gameName } else { "Desconhecido (AppID: $appID)" }
                PastaJogo   = $installDir
                Executaveis = if ($exes.Count -gt 0) { $exes -join ', ' } else { 'Nenhum encontrado' }
                Caminho     = $gamePath
            })
        } catch {
            Write-Warning "Erro ao processar manifesto: $($manifest.Name)"
        }
    }
}

# Mostrar resultados formatados
if ($gamesList.Count -gt 0) {
    $gamesList | Sort-Object NomeReal | Format-Table -Property AppID, NomeReal, PastaJogo, Executaveis -AutoSize -Wrap
    Write-Host "`nTotal de jogos encontrados: $($gamesList.Count)" -ForegroundColor Cyan
    Write-Host "Bibliotecas com erro foram ignoradas (ver avisros acima)" -ForegroundColor Yellow
} else {
    Write-Host "Nenhum jogo Steam encontrado nas bibliotecas válidas" -ForegroundColor Red
}

# Exportar opcional para CSV
$gamesList | Export-Csv -Path "$env:USERPROFILE\Desktop\SteamGames.csv" -NoTypeInformation -Encoding UTF8