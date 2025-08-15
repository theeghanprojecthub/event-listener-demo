# Real-Time Log Forwarding Agent

This project is a robust, policy-based log forwarding agent. It uses a custom Python script to "tail" a source log file in real-time, enrich the new log entries with a signature, and forward them to a destination file.

The agent is designed for maximum flexibility and can be run in multiple ways: as a simple local script, as a portable Docker container, or as a professional, auto-restarting service on a production Linux server.

-----

## Features

  * **Real-time Log Tailing:** Continuously monitors a source file and processes new data as it's written.
  * **Content Enrichment:** Adds a timestamped signature to each forwarded log line for clear traceability.
  * **Rule-Based Configuration:** Uses separate, simple JSON files to define the source file (`monitor_rules.json`) and the destination file (`action_rules.json`).
  * **Multiple Execution Modes:** Can be run directly with Python, as a local background script, via Docker, or as a robust `systemd` service.
  * **Automated Releases:** New versions are automatically built and published to GitHub Releases using GitHub Actions.
  * **Professional Installation:** A one-line installation script (`install.sh`) sets up the agent as a secure, managed service on Linux.
  * **CLI Management Tool:** Includes a `log-agent-ctl` utility for easy post-installation management of the service's configuration.

-----

## Project Structure

```
.
├── .github/workflows/         # GitHub Actions for releases
├── Dockerfile                 # For building the Docker image
├── agent.py                   # The core agent logic
├── docker-compose.yml         # For running the agent with Docker
├── log_generator.py           # Utility to simulate log traffic
├── monitor_rules.json         # Default monitoring rules
├── action_rules.json          # Default action rules
├── install.sh                 # Installation script for Linux service
├── log-agent-ctl              # Post-installation management tool
├── run_local.sh               # Script to run agent locally in background
├── run_monitor.sh             # Script to manage the Docker container
└── requirements.txt           # Build-time dependencies (PyInstaller)
```

-----

## How to Run (For Users)

Choose the method that best fits your needs.

### Method 1: Linux Service Installation (Recommended for Servers)

This is the most robust method for running the agent 24/7 on a production Linux server. It installs the agent as a system service that starts on boot and restarts automatically.

1.  **Run the Installer:**
    Execute the following command on your server. You must replace `your-github-username/your-repo-name` with the actual repository path.

    ```bash
    read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN && \
    curl -sSL -H "Authorization: token $GITHUB_TOKEN" \
    https://raw.githubusercontent.com/theeghanprojecthub/event-listener-demomain/install.sh | sudo -E bash
    ```

2.  **Manage the Agent:**
    After installation, you can manage the agent using the new `log-agent-ctl` command.

      * **Get Help:**
        ```bash
        log-agent-ctl help
        ```
      * **View Current Configuration:**
        ```bash
        log-agent-ctl show-config
        ```
      * **Change the Source Log File:**
        ```bash
        sudo log-agent-ctl set-source /var/log/syslog
        ```

### Method 2: Run with Docker

This method is highly portable and works on any system with Docker installed.

1.  **Start the Agent:**
    Use the provided management script to build and run the container.

    ```bash
    chmod +x run_monitor.sh
    ./run_monitor.sh start
    ```

2.  **Manage the Agent:**

      * **View Logs:** `./run_monitor.sh logs`
      * **Stop:** `./run_monitor.sh stop`
      * **Restart:** `./run_monitor.sh restart`

### Method 3: Local Background Script (for macOS & Linux)

This method runs the agent as a background process on your local machine without needing Docker.

1.  **Start the Agent:**

    ```bash
    chmod +x run_local.sh
    ./run_local.sh start
    ```

2.  **Manage the Agent:**

      * **Check Status:** `./run_local.sh status`
      * **View Logs:** `./run_local.sh logs`
      * **Stop:** `./run_local.sh stop`

-----

## For Developers

### Running from Source

For debugging and development, you can run the agent directly.

1.  **Prerequisites:** Ensure Python 3 is installed.
2.  **Run Agent:**
    ```bash
    python agent.py
    ```
    The agent will run in the foreground of your terminal. Press `Ctrl+C` to stop it.

### Release Process

This repository uses **GitHub Actions** to automate the release process. When a new version tag (e.g., `v1.0.1`) is pushed to the `main` branch, a workflow is triggered. This workflow uses **PyInstaller** to compile the `agent.py` script into a single, dependency-free binary. It then creates a new **GitHub Release** and uploads the compiled binary along with the default `monitor_rules.json` and `action_rules.json` files as release assets. This automated process makes new versions of the agent immediately available for the Linux service installation method.