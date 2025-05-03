# ER_Sync.ps1

# Configurações
$RclonePath = "D:\messi\Documents\rclone\rclone.exe"    #Diretorio do rclone
$CloudRemote = "onedrive"                               # Nome do remote configurado no rclone
$CloudDir = "SaveGames/EldenRing"                       # Diretório remoto no OneDrive
$LocalDir = "$env:APPDATA\EldenRing"                    # Diretório local para saves
$GameProcess = "eldenring"                              # Nome do processo do jogo
$GameExePath = "F:\messi\Games\Steam\steamapps\common\ELDEN RING\Game\ersc_launcher.exe"  # Caminho do executável do jogo


# Criar diretórios se não existirem
if (-not (Test-Path -Path $LocalDir)) {
    try {
        New-Item -ItemType Directory -Path $LocalDir -ErrorAction Stop | Out-Null
    }   
    catch {
        Write-Host "Erro ao criar diretório local: $_" -ForegroundColor Red
        exit 1
    }
}

# Criar diretório remoto
try {
    & $RclonePath mkdir "$($CloudRemote):$($CloudDir)"
}
catch {
    Write-Host "Erro ao criar diretório remoto: $_" -ForegroundColor Red
    exit 1
}

# Função de sincronização bidirecional
function Sync-Saves {
    Write-Host "Sincronizando saves..."

    # Fase 1: Baixar da nuvem
    try {
        & $RclonePath copy "$($CloudRemote):$($CloudDir)/" "$LocalDir/" `
            --progress `
            --update `
            --create-empty-src-dirs
    }
    catch {
        Write-Host "Erro ao baixar da nuvem: $_" -ForegroundColor Red
        exit 1
    }

    # Fase 2: Enviar para a nuvem
    try {
        & $RclonePath copy "$LocalDir/" "$($CloudRemote):$($CloudDir)/" `
            --progress `
            --update `
            --create-empty-src-dirs
    }
    catch {
        Write-Host "Erro ao enviar para a nuvem: $_" -ForegroundColor Red
        exit 1
    }
}

# Etapa 1: Sincronização inicial
Sync-Saves

# Etapa 2: Iniciar o jogo
Write-Host "Iniciando o jogo..."
Start-Process -FilePath $GameExePath -PassThru

# Esperar inicialização do processo
Write-Host "Aguardando o jogo iniciar..."
do {
    Start-Sleep -Seconds 5
    $process = Get-Process -Name $GameProcess -ErrorAction SilentlyContinue
} until ($process)

# Etapa 3: Monitorar fechamento do jogo
Write-Host "Aguardando o jogo fechar..."
do {
    Start-Sleep -Seconds 5
    $process = Get-Process -Name $GameProcess -ErrorAction SilentlyContinue
} while ($process)

# Garantir liberação de recursos
Start-Sleep -Seconds 1

# Etapa 4: Sincronização final
Sync-Saves

# Manter terminal aberto
Write-Host "Sincronização concluída!"
# Read-Host -Prompt "Pressione Enter para sair..."