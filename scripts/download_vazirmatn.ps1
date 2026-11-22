# Fetch official Vazirmatn v33.003 (SIL Open Font License 1.1).
# Intentionally fail the Windows build if the font is absent or corrupt.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$fontDir = Join-Path $root 'assets\fonts'
New-Item -ItemType Directory -Force -Path $fontDir | Out-Null
$regular = Join-Path $fontDir 'Vazirmatn-Regular.ttf'

function Assert-Font([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing font file: $path"
    }
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -lt 40000) { throw "Invalid font size: $path" }
    $ttf = ($bytes[0] -eq 0 -and $bytes[1] -eq 1 -and $bytes[2] -eq 0 -and $bytes[3] -eq 0)
    $otf = ([System.Text.Encoding]::ASCII.GetString($bytes, 0, 4) -eq 'OTTO')
    if (-not $ttf -and -not $otf) { throw "Invalid TTF/OTF signature: $path" }
}

if (Test-Path -LiteralPath $regular) {
    Assert-Font $regular
    Write-Host "Official Vazirmatn font already available."
    exit 0
}

$archive = Join-Path $env:TEMP ('vazirmatn_' + [guid]::NewGuid().ToString('N') + '.zip')
$unpack = Join-Path $env:TEMP ('vazirmatn_' + [guid]::NewGuid().ToString('N'))
try {
    $url = 'https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/vazirmatn-v33.003.zip'
    Write-Host "Downloading official Vazirmatn release..."
    Invoke-WebRequest -Uri $url -OutFile $archive -MaximumRedirection 10
    Expand-Archive -LiteralPath $archive -DestinationPath $unpack -Force

    foreach ($weight in @('Regular', 'Medium', 'SemiBold', 'Bold')) {
        $name = "Vazirmatn-$weight.ttf"
        $match = Get-ChildItem -Path $unpack -Filter $name -Recurse -File | Select-Object -First 1
        if ($null -ne $match) {
            $dest = Join-Path $fontDir $name
            Copy-Item -LiteralPath $match.FullName -Destination $dest -Force
            Assert-Font $dest
            Write-Host "Packed: $name"
        }
    }
    Assert-Font $regular

    $license = Get-ChildItem -Path $unpack -Recurse -File |
        Where-Object { $_.Name -match '^(OFL|OFL\.txt|LICENSE|LICENSE\.txt)$' } |
        Select-Object -First 1
    if ($license) {
        Copy-Item -LiteralPath $license.FullName -Destination (Join-Path $fontDir 'OFL.txt') -Force
    }
} finally {
    Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $unpack -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host 'Vazirmatn files validated successfully.'
