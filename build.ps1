# Build from the tested Windows Python environment.
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    python -m compileall -q app.py main.py
    if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed." }
    python -m PyInstaller --noconfirm --clean Wachsam.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
    Write-Host "Build ready: dist\Wachsam\Wachsam.exe"
    Write-Host "Keep the complete dist\Wachsam folder together."
} finally {
    Pop-Location
}
