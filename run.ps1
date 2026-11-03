# Start from source without relying on the terminal working directory.
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    python app.py
    if ($LASTEXITCODE -ne 0) { throw "Application exited with an error." }
} finally {
    Pop-Location
}
