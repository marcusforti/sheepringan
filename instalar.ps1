# Instala a skill sheepringan no Windows, sem admin e sem Git.
# irm https://raw.githubusercontent.com/marcusforti/sheepringan/main/instalar.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $tmp = Join-Path $env:TEMP ('sheepringan-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $repo = $env:SHEEPRINGAN_ORIGEM
    if (-not $repo) {
        $zip = Join-Path $tmp 'repo.zip'
        Invoke-WebRequest 'https://github.com/marcusforti/sheepringan/archive/refs/heads/main.zip' -OutFile $zip -UseBasicParsing
        Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force
        $repo = Join-Path $tmp 'sheepringan-main'
    }
    $origem = Join-Path $repo 'skill\sheepringan'
    if (-not (Test-Path (Join-Path $origem 'SKILL.md'))) { throw 'Nao achei a skill no pacote baixado.' }
    $alvos = @((Join-Path $env:USERPROFILE '.claude\skills'), (Join-Path $env:USERPROFILE '.agents\skills'))
    foreach ($alvo in $alvos) {
        New-Item -ItemType Directory -Force $alvo | Out-Null
        $destino = Join-Path $alvo 'sheepringan'
        $novo = "$destino.novo"
        $velho = "$destino.velho"
        Remove-Item -Recurse -Force $novo, $velho -ErrorAction SilentlyContinue
        # Monta a pasta nova ao lado e troca no fim: se algo falhar no meio, a versao antiga continua inteira.
        Copy-Item -Recurse -Force $origem $novo
        Get-ChildItem $novo -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force
        if (Test-Path $destino) { Rename-Item $destino 'sheepringan.velho' }
        Rename-Item $novo 'sheepringan'
        Remove-Item -Recurse -Force $velho -ErrorAction SilentlyContinue
    }
    Write-Host ''
    Write-Host 'sheepringan instalada.' -ForegroundColor Green
    Write-Host 'Abra o Claude Code (se ja estava aberto, feche e abra de novo) e escreva: /sheepringan'
    Write-Host ''
    Write-Host 'O que o seu computador precisa ter (a skill confere e ajuda a instalar):'
    foreach ($par in @(@('python', 'Python 3.9 ou mais novo'), @('ffmpeg', 'ffmpeg (winget install Gyan.FFmpeg)'), @('ssh', 'Cliente OpenSSH (Configuracoes > Aplicativos > Recursos opcionais)'))) {
        if (Get-Command $par[0] -ErrorAction SilentlyContinue) { Write-Host ('  ok     ' + $par[0]) } else { Write-Host ('  FALTA  ' + $par[1]) -ForegroundColor Yellow }
    }
} catch {
    Write-Host "Nao consegui instalar: $_" -ForegroundColor Red
} finally {
    if ($tmp -and (Test-Path $tmp)) { Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue }
}
