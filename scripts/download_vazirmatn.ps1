# Downloads the official open-source Vazirmatn release (SIL OFL 1.1).
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$destination = Join-Path $root 'assets\fonts\Vazirmatn-Regular.ttf'
if (Test-Path $destination) {
    Write-Host 'Vazirmatn font is already present.'
    exit 0
}
$archive = Join-Path $env:TEMP ('vazirmatn_' + [guid]::NewGuid().ToString('N') + '.zip')
$unpack = Join-Path $env:TEMP ('vazirmatn_' + [guid]::NewGuid().ToString('N'))
try {
    $url = 'https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/vazirmatn-v33.003.zip'
    Write-Host 'Downloading Vazirmatn from the official GitHub release...'
    Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing
    Expand-Archive -Path $archive -DestinationPath $unpack -Force
    $font = Get-ChildItem -Path $unpack -Recurse -Filter 'Vazirmatn-Regular.ttf' -File | Select-Object -First 1
    if (-not $font) { throw 'Regular TTF not found in release archive.' }
    Copy-Item -LiteralPath $font.FullName -Destination $destination -Force
    Write-Host ('Font saved to: ' + $destination)
} catch {
    Write-Warning ('Font download failed. UI will fall back to Tahoma. ' + $_.Exception.Message)
    exit 0
} finally {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $unpack -Recurse -Force -ErrorAction SilentlyContinue
}
