$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if ($env:OS -ne 'Windows_NT') { throw 'Build the Windows application on Windows.' }
python -c 'import tkinter; import sys; assert sys.version_info >= (3, 10)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ with Tkinter is required on the build machine.' }
python -m pip install --disable-pip-version-check 'pyinstaller==6.22.3'
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller installation failed.' }
python -m unittest -q tests test_engine test_features test_resources test_gui
if ($LASTEXITCODE -ne 0) { throw 'Rules or engine test failed.' }
python -m PyInstaller --clean --noconfirm hastings.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }
$portable = Join-Path $PSScriptRoot 'dist\HastingsChess'
$stage = Join-Path $env:TEMP ('Hastings Chess Portable Test ' + [Guid]::NewGuid().ToString('N'))
$errorLog = Join-Path $env:APPDATA 'Hastings Chess\launch-errors.log'
try {
    Copy-Item $portable $stage -Recurse
    Push-Location $env:WINDIR
    try {
        & (Join-Path $stage 'HastingsChess.exe') --smoke-test
        if ($LASTEXITCODE -ne 0) {
            if (Test-Path $errorLog) { Get-Content $errorLog -Tail 80 }
            throw 'Portable executable smoke test failed.'
        }
        & (Join-Path $stage 'HastingsChess.exe') --gui-smoke
        if ($LASTEXITCODE -ne 0) {
            if (Test-Path $errorLog) { Get-Content $errorLog -Tail 80 }
            throw 'Portable visible-GUI smoke test failed.'
        }
    } finally { Pop-Location }
} finally { Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
$archive = Join-Path $PSScriptRoot 'dist\HastingsChess_Windows_Portable.zip'
Compress-Archive -Path $portable -DestinationPath $archive -Force
Write-Host "Built and smoke-tested $archive"
