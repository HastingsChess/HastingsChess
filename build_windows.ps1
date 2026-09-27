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
$frozenExe = Join-Path $PSScriptRoot 'dist\HastingsChess.exe'
if (-not (Test-Path -LiteralPath $frozenExe)) { throw 'One-file executable was not produced.' }
if (Test-Path -LiteralPath $portable) { Remove-Item -LiteralPath $portable -Recurse -Force }
New-Item -ItemType Directory -Path $portable | Out-Null
Copy-Item -LiteralPath $frozenExe -Destination (Join-Path $portable 'HastingsChess.exe')
$guideName = 'Honestly, you should probably read this at some point.txt'
$guide = Join-Path $PSScriptRoot $guideName
Copy-Item -LiteralPath $guide -Destination (Join-Path $portable $guideName)
$archive = Join-Path $PSScriptRoot 'dist\HastingsChess_Windows_Portable.zip'
Compress-Archive -Path $portable -DestinationPath $archive -Force
$stage = Join-Path $env:TEMP ('Hastings Chess Portable Test ' + [Guid]::NewGuid().ToString('N'))
$errorLog = Join-Path $env:APPDATA 'Hastings Chess\launch-errors.log'
try {
    Expand-Archive -LiteralPath $archive -DestinationPath $stage
    $extracted = Join-Path $stage 'HastingsChess'
    $exe = Join-Path $extracted 'HastingsChess.exe'
    $packagedGuide = Join-Path $extracted $guideName
    if (-not (Test-Path -LiteralPath $exe) -or -not (Test-Path -LiteralPath $packagedGuide)) {
        throw 'Extracted ZIP is missing the executable or player documentation.'
    }
    if ((Get-FileHash -LiteralPath $guide -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $packagedGuide -Algorithm SHA256).Hash) {
        throw 'Packaged player documentation differs from approved source text.'
    }
    # A fresh recipient has no build-machine Python/Tcl search paths. Poison
    # inherited Tcl paths to prove the PyInstaller runtime hook replaces them.
    $savedEnvironment = @{}
    foreach ($name in @('PATH','PYTHONHOME','PYTHONPATH','TCL_LIBRARY','TK_LIBRARY')) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    $env:PATH = "$env:WINDIR\System32;$env:WINDIR"
    $env:PYTHONHOME = Join-Path $stage 'nonexistent-python'
    $env:PYTHONPATH = Join-Path $stage 'nonexistent-modules'
    $env:TCL_LIBRARY = Join-Path $stage 'nonexistent-tcl'
    $env:TK_LIBRARY = Join-Path $stage 'nonexistent-tk'
    Push-Location $env:WINDIR
    try {
        $marker = Join-Path $extracted 'smoke-result.txt'
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
    } finally {
        Remove-Item Env:HASTINGS_SMOKE_MARKER -ErrorAction SilentlyContinue
        Pop-Location
        foreach ($name in $savedEnvironment.Keys) {
            [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
        }
    }
} finally { Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "Built and smoke-tested $archive"
exit 0
