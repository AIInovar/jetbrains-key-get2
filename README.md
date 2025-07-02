# JetBrains License Key Fetcher

A Python tool to fetch JetBrains IDE license keys from various online sources.

**Disclaimer**: This tool is for educational purposes only. Using license keys without proper authorization may violate JetBrains' terms of service. The authors are not responsible for any misuse of this tool.

## Features

- Fetches license keys from multiple online sources
- Supports concurrent requests for faster processing
- Caches results to avoid duplicate processing
- Validates license key formats
- Detailed logging for troubleshooting
- GitHub API integration for better access (optional)

## Requirements

- Python 3.6+
- Required packages listed in `requirements.txt`

## Installation

```bash
git clone https://github.com/relyadev/jetbrains-key-get
cd jetbrains-key-get
pip install -r requirements.txt
```

## Usage

```bash
python main.py [options]
```

### Options

- `--days N`: Number of days to look back for licenses (default: 30)
- `--output FILE`: Output file for saving licenses (default: jetbrains_licenses.txt)
- `--workers N`: Maximum concurrent workers (default: 5)
- `--github-token TOKEN`: GitHub API token for increased rate limits (optional)
- `--log-file FILE`: Log file for detailed logging (default: fetcher.log)
- `--verbose`: Enable verbose logging
- `--version`: Show version information

### Example

```bash
python main.py --days 60 --workers 10 --verbose
```

## Fake License Server

This project includes a Docker-based fake license server that can serve the collected licenses to JetBrains IDEs.

### Requirements
- Docker
- Docker Compose

### Usage
1. Build and start the server:
   ```bash
   docker-compose up --build -d
   ```
2. Configure your JetBrains IDE:
   - Go to `Help > Register...`
   - Select "License server"
   - Enter: `http://localhost:8080/license`

3. Check server status:
   ```bash
   curl http://localhost:8080/status
   ```

### Alternative Docker Commands

If you don't have `docker-compose` installed, you can use these commands instead:

1. Build the Docker image:
   ```bash
   docker build -t jetbrains-license-server .
   ```
2. Run the container:
   ```bash
   docker run -d -p 8080:8080 -v ${PWD}/jetbrains_licenses.txt:/app/licenses.txt --name jetbrains-license-server jetbrains-license-server
   ```

For Windows PowerShell, use:
```powershell
docker run -d -p 8080:8080 -v ${PWD}/jetbrains_licenses.txt:/app/licenses.txt --name jetbrains-license-server jetbrains-license-server
```

### Notes
- The server will automatically reload licenses when the `jetbrains_licenses.txt` file is updated
- By default, it serves a random valid license from the collected keys
- The server runs on port 8080 (change in docker-compose.yml if needed)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
