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

    # Configurações da fonte (Montserrat - requer instalação)
    $montserratBold = [System.Drawing.FontFamily]::new("Montserrat")
    $montserratRegular = if ($null -ne $montserratBold) { $montserratBold } else { "Segoe UI" }
    if ($montserratRegular -eq $montserratBold) {
        Write-Log -Message "Usando fonte Montserrat" -Level "Info"
    }
    else {
        Write-Log -Message "Usando fonte Segoe UI" -Level "Info"
    }

   # Configurações do formulário
    $formWidth = 300
    $formHeight = 75
    $form = New-Object System.Windows.Forms.Form
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
    $form.Size = New-Object System.Drawing.Size($formWidth, $formHeight)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
    $form.BackColor = [System.Drawing.Color]::FromArgb(28, 32, 39)
    $form.TopMost = $true

    # Habilitar DoubleBuffered usando reflexão
    $formType = $form.GetType()
    $doubleBufferedProperty = $formType.GetProperty("DoubleBuffered", [System.Reflection.BindingFlags] "NonPublic, Instance")
    $doubleBufferedProperty.SetValue($form, $true, $null)

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
            $gradient.Dispose()
        }
    })

    # Ícones (ajuste os caminhos conforme necessário)
    # Atualiza o caminho dos assets para subir dois níveis e acessar "assets"
    $assetsPath = Join-Path -Path (Split-Path -Parent (Split-Path $PSScriptRoot)) -ChildPath "assets"
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

    # Controles
    $lblTitle = New-Object System.Windows.Forms.Label
    $lblTitle.Text = "CloudQuest"
    $lblTitle.Location = New-Object System.Drawing.Point(75, 15)
    $lblTitle.AutoSize = $true  # Permite que o label se ajuste ao texto
    $lblTitle.Font = New-Object System.Drawing.Font($montserratRegular, 7, [System.Drawing.FontStyle]::Bold)
    $lblTitle.ForeColor = [System.Drawing.Color]::FromArgb(140, 145, 151)
    $lblTitle.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

    $lblApp = New-Object System.Windows.Forms.Label
    $lblApp.Text = "$GameName"
    $lblApp.Location = New-Object System.Drawing.Point(75, 30)
    $lblApp.AutoSize = $true  # Permite que o label se ajuste ao texto
    $lblApp.Font = New-Object System.Drawing.Font($montserratRegular, 10, [System.Drawing.FontStyle]::Bold)
    $lblApp.ForeColor = [System.Drawing.Color]::White
    $lblApp.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

    $lblStatus = New-Object System.Windows.Forms.Label
    $lblStatus.Text = if ($Direction -eq "sync") { "Atualizando progresso..." } else { "Sincronizando a Nuvem..." }
    $lblStatus.Location = New-Object System.Drawing.Point(75, 52)
    $lblStatus.AutoSize = $true  # Permite que o label se ajuste ao texto
    $lblStatus.Font = New-Object System.Drawing.Font($montserratRegular, 7, [System.Drawing.FontStyle]::Regular)
    $lblStatus.ForeColor = [System.Drawing.Color]::FromArgb(140, 145, 151)
    $lblStatus.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário
    # Mensagem de status para erros
    $statusMessage = switch ($Type) {
        "error" {
            if ($Direction -eq "sync") { "Falha no Download!" } else { "Falha no Upload!" }
        }
        default {
            if ($Direction -eq "sync") { "Atualizando seu progresso..." } else { "Sincronizando a Nuvem..." }
        }
    }

    if ($Type -eq "error") {
        $lblStatus.Text = $statusMessage
        $lblStatus.ForeColor = [System.Drawing.Color]::FromArgb(220, 50, 50)  # Vermelho
    }

    $picIcon = New-Object System.Windows.Forms.PictureBox
    $picIcon.Location = New-Object System.Drawing.Point(10, 15)
    $picIcon.Size = New-Object System.Drawing.Size(55, 44)
    $picIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
    $picIcon.Image = [System.Drawing.Image]::FromFile($iconPath)
    $picIcon.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

    $bgIcon = New-Object System.Windows.Forms.PictureBox
    $bgIcon.Location = New-Object System.Drawing.Point(201, -4)
    $bgIcon.Size = New-Object System.Drawing.Size(103, 83)
    $bgIcon.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage
    $bgIcon.Image = [System.Drawing.Image]::FromFile($bgPath)
    $bgIcon.BackColor = [System.Drawing.Color]::Transparent  # Cor de fundo do formulário

    # Timer para fechar após 6 segundos
    $timer = New-Object System.Windows.Forms.Timer
    $timer.Interval = 6000
    $timer.Enabled = $true
    $timer.Add_Tick({ $form.Close(); $timer.Stop() })

    # Adicionar controles somente após todos os componentes estarem carregados
    $form.Opacity = 0
    $form.SuspendLayout()
    $panel.Controls.AddRange(@($lblTitle, $lblApp, $lblStatus, $picIcon, $bgIcon))
    $form.Controls.Add($panel)
    $form.ResumeLayout($false)
    $form.PerformLayout()
    $form.Add_Shown({ $form.Activate() })
    $form.Show()
    $form.Refresh()
    $form.Opacity = 1

    return @{ Form = $form; Timer = $timer }
}

# A função Show-CustomNotification implementa as notificações conforme o esperado.