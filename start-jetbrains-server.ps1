# Create necessary directories
New-Item -ItemType Directory -Force -Path ".\jetbrains-license-data\logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".\jetbrains-license-data\license-server" | Out-Null
New-Item -ItemType Directory -Force -Path ".\jetbrains-license-data\license-server\license-keys" | Out-Null

# Copy access config
Copy-Item -Path ".\access-config.json" -Destination ".\jetbrains-license-data\access-config.json" -Force

# Copy license keys if they exist
if (Test-Path ".\jetbrains_licenses.txt") {
    Copy-Item -Path ".\jetbrains_licenses.txt" -Destination ".\jetbrains-license-data\license-server\license-keys\jetbrains_licenses.txt" -Force
}

# Start the server
Write-Host "Starting JetBrains License Server..." -ForegroundColor Green
Write-Host "Access the web interface at: http://localhost:8111/jls" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

docker-compose -f .\docker-compose.jetbrains-server.yml up
