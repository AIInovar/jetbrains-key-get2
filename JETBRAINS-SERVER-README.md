# JetBrains License Server Setup

This directory contains the configuration for running a JetBrains License Server using Docker.

## ⚠️ Important Note

The official JetBrains License Server will be discontinued on December 31, 2025. 
Consider this a temporary solution and plan to migrate to JetBrains' new licensing system.

## Prerequisites

- Docker and Docker Compose installed
- At least 1GB of free disk space
- Port 8111 available

## Quick Start

1. **Start the server**:
   ```powershell
   .\start-jetbrains-server.ps1
   ```

2. **Access the web interface**:
   Open http://localhost:8111/jls in your browser

3. **Add license keys**:
   - Place your license keys in `jetbrains_licenses.txt` (one per line)
   - The server will automatically pick up the keys

## Configuration

### Ports
- `8111`: Web interface and API

### Volumes
- `./jetbrains-license-data`: Contains all server data
  - `logs/`: Server logs
  - `license-server/license-keys/`: Directory for license keys
  - `access-config.json`: Access control configuration

### Environment Variables
- `JLS_VENDOR_NAME`: Your company/organization name
- `JLS_ACCESS_CONFIG`: Path to access control config
- `JLS_SERVICE_LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- `JLS_SERVICE_LOG_PATH`: Path to log file
- `JLS_CONTEXT`: Base URL path (default: /jls)

## Security

By default, the server is only accessible from localhost and local network (172.x.x.x).
To modify access controls, edit `access-config.json`.

## Updating License Keys

1. Update the `jetbrains_licenses.txt` file
2. Restart the server for changes to take effect

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running, or run:

```powershell
docker-compose -f .\docker-compose.jetbrains-server.yml down
```

## Troubleshooting

Check the logs in `jetbrains-license-data/logs/` for any issues.

## License

This setup is provided as-is. Please ensure you have the right to use any license keys you add to the server.
