# PowerShell script to start the JetBrains fake license server

# Build the Docker image
docker build -t jetbrains-license-server .

# Check if container already exists and remove it
if (docker ps -a --format '{{.Names}}' | Select-String -Pattern 'jetbrains-license-server' -Quiet) {
    docker stop jetbrains-license-server
    docker rm jetbrains-license-server
}

# Run the container
docker run -d `
    -p 8080:8080 `
    -v "${PWD}/jetbrains_licenses.txt:/app/licenses.txt" `
    --name jetbrains-license-server `
    jetbrains-license-server

Write-Host "License server running at http://localhost:8080"
