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
$guideName = 'Honestly, you should probably read this at some point.txt'
$guide = Join-Path $PSScriptRoot $guideName
Copy-Item -LiteralPath $guide -Destination (Join-Path $portable $guideName)
$stage = Join-Path $env:TEMP ('Hastings Chess Portable Test ' + [Guid]::NewGuid().ToString('N'))
$errorLog = Join-Path $env:APPDATA 'Hastings Chess\launch-errors.log'
try {
    & robocopy $portable $stage /E /R:1 /W:1 | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "Portable folder copy failed: robocopy exit $LASTEXITCODE" }
    $exe = Join-Path $stage 'HastingsChess.exe'
    $tkScript = Join-Path $stage '_internal\_tk_data\ttk\altTheme.tcl'
    $engineBinary = Join-Path $stage '_internal\engine\fairy-stockfish.exe'
    $packagedGuide = Join-Path $stage $guideName
    if (-not (Test-Path $exe) -or -not (Test-Path $tkScript) -or -not (Test-Path $engineBinary) -or -not (Test-Path -LiteralPath $packagedGuide)) {
        throw 'Portable folder is missing the executable, Tk scripts, Fairy-Stockfish, or player documentation.'
    }
    if ((Get-FileHash -LiteralPath $guide -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $packagedGuide -Algorithm SHA256).Hash) {
        throw 'Packaged player documentation differs from approved source text.'
    }
    Push-Location $env:WINDIR
    try {
        $marker = Join-Path $stage 'smoke-result.txt'
        $env:HASTINGS_SMOKE_MARKER = $marker
        $smoke = Start-Process -FilePath $exe -ArgumentList '--smoke-test' -WorkingDirectory $env:WINDIR -Wait -PassThru
        if ($smoke.ExitCode -ne 0 -or -not (Test-Path $marker) -or (Get-Content $marker -Raw).Trim() -ne 'engine-ok') {
            if (Test-Path $errorLog) { Get-Content $errorLog -Tail 80 }
            throw 'Portable executable smoke test failed.'
        }
        Remove-Item $marker
        $guiSmoke = Start-Process -FilePath $exe -ArgumentList '--gui-smoke' -WorkingDirectory $env:WINDIR -Wait -PassThru
        if ($guiSmoke.ExitCode -ne 0 -or -not (Test-Path $marker) -or (Get-Content $marker -Raw).Trim() -ne 'gui-ok') {
            if (Test-Path $errorLog) { Get-Content $errorLog -Tail 80 }
            throw 'Portable visible-GUI smoke test failed.'
        }
        Remove-Item $marker
    } finally { Remove-Item Env:HASTINGS_SMOKE_MARKER -ErrorAction SilentlyContinue; Pop-Location }
} finally { Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
$archive = Join-Path $PSScriptRoot 'dist\HastingsChess_Windows_Portable.zip'
Compress-Archive -Path $portable -DestinationPath $archive -Force
Write-Host "Built and smoke-tested $archive"
exit 0
