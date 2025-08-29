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

VERSION=$(echo "$API_RESPONSE" | jq -r ".tag_name")
if [ -z "$VERSION" ] || [ "$VERSION" == "null" ]; then
    echo "Could not determine the latest version from the GitHub release. Aborting." >&2
    exit 1
fi

BINARY_URL=$(get_asset_url "$AGENT_BINARY_NAME")
if [ -z "$BINARY_URL" ]; then
    echo "Could not find the agent binary ('$AGENT_BINARY_NAME') in the latest GitHub release. Aborting." >&2
    exit 1
fi
echo "Downloading agent binary version $VERSION..."
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

# Final success message with ASCII art
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
cat << "EOF"
 __                _            _                    _
| |              | |          | |                  | |
| |     ___   ___| | ___   ___| |_ ____      ____ _| |_
| |    / _ \ / __| |/ _ \ / __| __|_  /    / __ \_  _|
| |___| (_) | (__| | (_) | (__| |_ / /    |  __/_| |_
|______\___/ \___|_|\___/ \___|\__/___|_____\___| |___|
                                     /_____|
EOF
echo -e "${NC}"
echo "✅ Installation Complete!"
echo ""
echo -e "   Version: ${CYAN}$VERSION${NC}"
echo -e "   Status:  ${GREEN}Active (running)${NC}"
echo ""
echo "--------------------------------------------------"
echo "   Next Steps:"
echo "   1. Configure your sources and destinations with 'log-agent-ctl help'"
echo "   2. View the agent's live logs with 'sudo journalctl -u log-agent.service -f'"
echo "--------------------------------------------------"

