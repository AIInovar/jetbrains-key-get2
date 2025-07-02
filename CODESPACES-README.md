# JetBrains License Server on GitHub Codespaces

This guide explains how to run the JetBrains License Server using GitHub Codespaces.

## Prerequisites

- A GitHub account
- GitHub Codespaces enabled for your account

## Quick Start

1. **Open in GitHub Codespaces**
   - Click the "Code" button on your repository
   - Select "Open with Codespaces"
   - Choose "New codespace"

2. **Start the Server**
   ```bash
   chmod +x start-codespaces.sh
   ./start-codespaces.sh
   ```

3. **Access the Web Interface**
   - The server will be available at: `https://<your-codespace-name>-8111.app.github.dev/jls`
   - GitHub will show a notification with the URL when the server starts

## Features

- Automatic HTTPS with GitHub's domain
- Persistent storage for license keys
- Access from anywhere with internet
- No credit card required

## Important Notes

- The server will stop when the codespace is stopped
- Data persists between sessions as long as the codespace exists
- Free tier includes 120 core hours per month

## Managing License Keys

1. Add your license keys to `jetbrains_licenses.txt`
2. Restart the server to apply changes

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

Check the logs in `jetbrains-license-data/logs/` for any issues.
