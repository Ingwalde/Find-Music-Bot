$ErrorActionPreference = "Stop"

$filesToRemove = @(
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "requirements-dev.txt"
)

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "Removed $file"
    }
}

Write-Host "v2.5.2 deploy/ and requirements/ cleanup completed."
