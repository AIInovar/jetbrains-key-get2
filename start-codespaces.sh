#!/bin/bash

# Create necessary directories
mkdir -p jetbrains-license-data/logs
mkdir -p jetbrains-license-data/license-server/license-keys

# Copy configuration files
cp access-config.json jetbrains-license-data/
cp jetbrains_licenses.txt jetbrains-license-data/license-server/license-keys/ 2>/dev/null || true

# Set permissions
chmod -R 777 jetbrains-license-data

# Start the server
echo "Starting JetBrains License Server..."
echo "Access the web interface at: https://$CODESPACE_NAME-8111.app.github.dev/jls"

docker-compose -f docker-compose.jetbrains-server.yml up
