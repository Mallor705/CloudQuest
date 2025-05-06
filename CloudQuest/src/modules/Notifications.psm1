# NOTIFICAÇÕES PERSONALIZADAS (ATUALIZADA)
# ====================================================
function Show-CustomNotification {
    param(
        [string]$Title,
        [string]$Message,
        [string]$Type = "info",
        [string]$Direction = "sync"  # Novo parâmetro para direção (sync/update)
    )

    Write-Log -Message "$Title - $Message" -Level $(if ($Type -eq "error") { "Error" } else { "Info" })

    # Tratamento de erro - Resposta segura para casos extremos
    if ($null -eq $PSScriptRoot) {
        Write-Log -Message "ERRO: PSScriptRoot é nulo" -Level Error
        return $null
    }

    # Configurações da fonte (Montserrat - requer instalação)
    try {
        $montserratBold = [System.Drawing.FontFamily]::new("Montserrat")
        $montserratRegular = if ($null -ne $montserratBold) { $montserratBold } else { "Segoe UI" }
        if ($montserratRegular -eq $montserratBold) {
            Write-Log -Message "Usando fonte Montserrat" -Level "Info"
        }
        else {
            Write-Log -Message "Usando fonte Segoe UI" -Level "Info"
        }
    }
    catch {
        # Fallback para fontes do sistema
        Write-Log -Message "Erro ao carregar fonte, usando sistema: $_" -Level Warning
        $montserratRegular = "Segoe UI"
    }

    # Configurações do formulário
    $formWidth = 300
    $formHeight = 75
    
    try {
        $form = New-Object System.Windows.Forms.Form
        $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
        $form.Size = New-Object System.Drawing.Size($formWidth, $formHeight)
        $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
        $form.BackColor = [System.Drawing.Color]::FromArgb(28, 32, 39)
        $form.TopMost = $true

        # Habilitar DoubleBuffered usando reflexão
        if ($null -ne $form) {
            $formType = $form.GetType()
            $doubleBufferedProperty = $formType.GetProperty("DoubleBuffered", [System.Reflection.BindingFlags] "NonPublic, Instance")
            if ($null -ne $doubleBufferedProperty) {
                $doubleBufferedProperty.SetValue($form, $true, $null)
            }
        }

        # Posicionamento baseado na direção
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
        $rightPosition = $screen.Right - 300
        if ($Direction -eq "sync") {
            $form.Location = New-Object System.Drawing.Point($rightPosition, 980)
        } else {
            $form.Location = New-Object System.Drawing.Point($rightPosition, 980)
        }

        # Painel com gradiente
        $panel = New-Object System.Windows.Forms.Panel
        $panel.Dock = [System.Windows.Forms.DockStyle]::Fill
        $panel.Add_Paint({
            param($sender, $e)
            
            if ($null -eq $e -or $null -eq $e.Graphics) {
                return
            }
            
            # Verifica se o sender e ClientRectangle são válidos
            if ($null -eq $sender -or $sender.ClientRectangle.IsEmpty) {
                $rect = New-Object System.Drawing.Rectangle(0, 0, $panel.Width, $panel.Height)
            }
            else {
                $rect = $sender.ClientRectangle
            }
        
            # Define as cores e o modo do gradiente
            $startColor = [System.Drawing.Color]::FromArgb(17, 23, 30)
            $endColor = [System.Drawing.Color]::FromArgb(28, 32, 39)
            $mode = [System.Drawing.Drawing2D.LinearGradientMode]::Vertical
        
            # Cria o gradiente
            $gradient = New-Object System.Drawing.Drawing2D.LinearGradientBrush(
                $rect,
                $startColor,
                $endColor,
                $mode
            )
        
            try {
                $e.Graphics.FillRectangle($gradient, $rect)
            }
            catch {
                Write-Log -Message "Erro ao renderizar gradiente: $_" -Level Error
            }
            finally {
                if ($null -ne $gradient) {
                    $gradient.Dispose()
                }
            }
        })

        # Ícones (ajuste os caminhos conforme necessário)
        # Atualiza o caminho dos assets para subir dois níveis e acessar "assets"
        $assetsPath = Join-Path -Path (Split-Path -Parent (Split-Path $PSScriptRoot)) -ChildPath "assets\icons"
        $iconBaseName = if ($Type -eq "error") { "error_" } else { "" }
        $bgBaseName = if ($Type -eq "error") { "error_" } else { "" }

        $iconPath = if ($Direction -eq "sync") { 
            Join-Path -Path $assetsPath -ChildPath "${iconBaseName}down.png"
        } else { 
            Join-Path -Path $assetsPath -ChildPath "${iconBaseName}up.png" 
        }
        
        $bgPath = if ($Direction -eq "sync") {
            Join-Path -Path $assetsPath -ChildPath "${bgBaseName}down_background.png"
        } else {
            Join-Path -Path $assetsPath -ChildPath "${bgBaseName}up_background.png"
        }

        # Verifica se os arquivos de ícones existem
        if (-not (Test-Path $iconPath)) {
            Write-Log -Message "AVISO: Ícone não encontrado: $iconPath" -Level Warning
            # Usar caminho alternativo ou ícone padrão
        }
        if (-not (Test-Path $bgPath)) {
            Write-Log -Message "AVISO: Background não encontrado: $bgPath" -Level Warning
            # Usar caminho alternativo ou background padrão
        }

        # Controles
        $lblTitle = New-Object System.Windows.Forms.Label
        $lblTitle.Text = "CloudQuest"
        $lblTitle.Location = New-Object System.Drawing.Point(75, 15)
        $lblTitle.AutoSize = $true  # Permite que o label se ajuste ao texto
        $lblTitle.Font = New-Object System.Drawing.Font($montserratRegular, 7, [System.Drawing.FontStyle]::Bold)
        $lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(140, 145, 151)
        $lblTitle.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

        $lblApp = New-Object System.Windows.Forms.Label
        $lblApp.Text = "$(if ($null -ne $GameName) { $GameName } else { "Jogo" })"
        $lblApp.Location = New-Object System.Drawing.Point(75, 30)
        $lblApp.AutoSize = $true  # Permite que o label se ajuste ao texto
        $lblApp.Font = New-Object System.Drawing.Font($montserratRegular, 10, [System.Drawing.FontStyle]::Bold)
        $lblApp.ForeColor = [System.Drawing.Color]::White
        $lblApp.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

        $lblStatus = New-Object System.Windows.Forms.Label
        # Define a mensagem de status combinando Type e Direction
        $statusMessage = switch ($Type) {
            "error" {
                # Mensagem de erro específica para a direção
                if ($Direction -eq "sync") { "Falha no download!" } else { "Falha no upload!" }
            }
            default {
                # Mensagem padrão baseada na direção
                if ($Direction -eq "sync") { "Atualizando seu progresso..." } else { "Sincronizando a nuvem..." }
            }
        }

        $lblStatus.Text = $statusMessage
        $lblStatus.Location = New-Object System.Drawing.Point(75, 52)
        $lblStatus.AutoSize = $true  # Permite que o label se ajuste ao texto
        $lblStatus.Font = New-Object System.Drawing.Font($montserratRegular, 7, [System.Drawing.FontStyle]::Regular)
        # Aplica a cor baseada no tipo
        $lblStatus.ForeColor = if ($Type -eq "error") { 
            [System.Drawing.Color]::FromArgb(220, 50, 50)  # Vermelho para erros
        } else { 
            [System.Drawing.Color]::FromArgb(140, 145, 151)  # Cinza para info
        }
        $lblStatus.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

        # Configuração dos ícones
        try {
            $picIcon = New-Object System.Windows.Forms.PictureBox
            $picIcon.Location = New-Object System.Drawing.Point(10, 15)
            $picIcon.Size = New-Object System.Drawing.Size(55, 44)
            $picIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
            if (Test-Path $iconPath) {
                $picIcon.Image = [System.Drawing.Image]::FromFile($iconPath)
            }
            $picIcon.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

            $bgIcon = New-Object System.Windows.Forms.PictureBox
            $bgIcon.Location = New-Object System.Drawing.Point(201, -4)
            $bgIcon.Size = New-Object System.Drawing.Size(103, 83)
            $bgIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
            if (Test-Path $bgPath) {
                $bgIcon.Image = [System.Drawing.Image]::FromFile($bgPath)
            }
            $bgIcon.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário
        }
        catch {
            Write-Log -Message "Erro ao carregar imagens: $_" -Level Error
        }

        # Timer para fechar após 5 segundos
        $timer = New-Object System.Windows.Forms.Timer
        $timer.Interval = 5000
        $timer.Enabled = $true
        $timer.Add_Tick({ 
            if ($null -ne $form -and -not $form.IsDisposed) {
                $form.Close()
            }
            $timer.Stop() 
        })

        # Adicionar controles somente após todos os componentes estarem carregados
        $form.Opacity = 0
        $form.SuspendLayout()
        
        # Verifica se os controles são válidos antes de adicioná-los
        $controlsToAdd = @()
        if ($null -ne $lblTitle) { $controlsToAdd += $lblTitle }
        if ($null -ne $lblApp) { $controlsToAdd += $lblApp }
        if ($null -ne $lblStatus) { $controlsToAdd += $lblStatus }
        if ($null -ne $picIcon) { $controlsToAdd += $picIcon }
        if ($null -ne $bgIcon) { $controlsToAdd += $bgIcon }
        
        if ($controlsToAdd.Count -gt 0) {
            $panel.Controls.AddRange($controlsToAdd)
        }
        
        $form.Controls.Add($panel)
        $form.ResumeLayout($false)
        $form.PerformLayout()
        
        # Modifica a lógica do Add_Shown para evitar erros de nulos
        $form.Add_Shown({
            try {
                if (-not $form.IsDisposed) {
                    $form.Activate()
                }
            }
            catch {
                Write-Log -Message "Erro no evento Shown: $_" -Level Error
            }
        })
        
        # Verifica se o formulário não foi descartado antes de exibi-lo
        if (-not $form.IsDisposed) {
            $form.Show()
            $form.Refresh()
            $form.Opacity = 1
        }

        return @{ Form = $form; Timer = $timer }
    }
    catch {
        Write-Log -Message "ERRO CRÍTICO na notificação: $_" -Level Error
        return $null  # Retorna nulo em caso de erro para não quebrar o fluxo
    }
}

# Exporta a função para uso em outros módulos
Export-ModuleMember -Function Show-CustomNotification