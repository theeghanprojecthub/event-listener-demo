#!/bin/bash

set -e

GITHUB_REPO="theeghanprojecthub/event-listener-demo"
INSTALL_DIR="/opt/log-forwarder-agent"
CONFIG_DIR="/etc/log-forwarder-agent"
LOG_DIR_SOURCE="/var/log/source_logs"
LOG_DIR_DEST="/var/log/destination_logs"
SERVICE_USER="logagent"
SERVICE_FILE="/etc/systemd/system/log-agent.service"
AGENT_BINARY_NAME="log-agent"
CTL_SCRIPT_NAME="log-agent-ctl"
AUTH_HEADER=""

echo ">>> Starting Log Forwarding Agent installation..."

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Please use 'sudo'." >&2
  exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "'jq' is not installed, but it is required for this installer." >&2
    echo "Please install it using your package manager (e.g., 'sudo apt-get update && sudo apt-get install -y jq')." >&2
    exit 1
fi

if [ -n "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN found. Using authenticated requests for a private repository."
    AUTH_HEADER="-H \"Authorization: token $GITHUB_TOKEN\""
fi

echo "Creating system user '$SERVICE_USER'..."
if ! id -u "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --shell /usr/sbin/nologin "$SERVICE_USER"
fi

echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR_SOURCE"
mkdir -p "$LOG_DIR_DEST"

echo "Fetching latest release from GitHub..."
LATEST_RELEASE_URL="https://api.github.com/repos/$GITHUB_REPO/releases/latest"

API_RESPONSE=$(curl -s $AUTH_HEADER "$LATEST_RELEASE_URL")

get_asset_url() {
    echo "$API_RESPONSE" | jq -r ".assets[] | select(.name == \"$1\") | .browser_download_url"
}

BINARY_URL=$(get_asset_url "$AGENT_BINARY_NAME")
if [ -z "$BINARY_URL" ]; then
    echo "Could not find the agent binary ('$AGENT_BINARY_NAME') in the latest GitHub release. Aborting." >&2
    exit 1
fi
echo "Downloading agent binary..."
# The URL for release assets does not require the auth header for downloading
curl -L -o "$INSTALL_DIR/$AGENT_BINARY_NAME" "$BINARY_URL"

MONITOR_RULES_URL=$(get_asset_url "monitor_rules.json")
ACTION_RULES_URL=$(get_asset_url "action_rules.json")
echo "Downloading default configuration files..."
curl -L -o "$CONFIG_DIR/monitor_rules.json" "$MONITOR_RULES_URL"
curl -L -o "$CONFIG_DIR/action_rules.json" "$ACTION_RULES_URL"

echo "Installing management tool '$CTL_SCRIPT_NAME'..."
CTL_URL="https://raw.githubusercontent.com/$GITHUB_REPO/main/$CTL_SCRIPT_NAME"
curl -sSL $AUTH_HEADER -o "/usr/local/bin/$CTL_SCRIPT_NAME" "$CTL_URL"
chmod +x "/usr/local/bin/$CTL_SCRIPT_NAME"

echo "Setting permissions..."
chown -R "$SERVICE_USER":"$SERVICE_USER" "$CONFIG_DIR"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$LOG_DIR_SOURCE"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$LOG_DIR_DEST"
chown root:root "$INSTALL_DIR/$AGENT_BINARY_NAME"
chmod 755 "$INSTALL_DIR/$AGENT_BINARY_NAME"

echo "Creating systemd service file..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Log Forwarding Agent Service
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$CONFIG_DIR
ExecStart=$INSTALL_DIR/$AGENT_BINARY_NAME
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting the service..."
systemctl daemon-reload
systemctl enable log-agent.service
systemctl start log-agent.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "The Log Forwarding Agent is now running."
echo "--------------------------------------------------"
echo "A new management tool has been installed: 'log-agent-ctl'"
echo ""
echo "Usage:"
echo "  log-agent-ctl help             - Show available commands and usage."
echo "  log-agent-ctl show-config      - View the current source and destination files."
echo "  sudo log-agent-ctl set-source <path> - Change the file to monitor."
echo ""
echo "System Service Commands:"
echo "  sudo systemctl status log-agent.service - Check agent status."
echo "  sudo journalctl -u log-agent.service -f - View live agent logs."
echo "--------------------------------------------------"
