# Real-Time Log Forwarding Agent

This project is a robust, policy-based log forwarding agent designed for maximum flexibility. It uses a custom Python script to monitor **multiple source log files** in real-time and forward new data to **multiple destinations** simultaneously, including local files, remote syslog servers, and HTTP endpoints.

The agent is designed for a variety of use cases and can be run directly with Python, as a local background script, via Docker, or as a professional, auto-restarting `systemd` service on a production Linux server.

-----

## Features

  * **Multi-Source & Multi-Destination:** Monitor multiple log files at once and route them to any combination of destinations.
  * **Advanced Log Routing:** Configure specific sources to go to specific destinations (e.g., security logs go to an HTTP alert endpoint, while application logs go to a central syslog server).
  * **Multiple Protocols:** Natively supports forwarding to local files, remote syslog (UDP with optional token-in-message authentication), and HTTP/S endpoints (with optional Bearer token authentication).
  * **Automated Releases:** New versions are automatically built into a single binary using PyInstaller and published to GitHub Releases via GitHub Actions.
  * **Professional Installation:** A one-line installation script (`install.sh`) sets up the agent as a secure, managed `systemd` service on Linux.
  * **Powerful CLI Management Tool:** Includes a `log-agent-ctl` utility for easy post-installation management of sources, destinations, and the links between them, including a full uninstall command.

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
└── requirements.txt           # Build-time dependencies (PyInstaller, requests)
```

-----

## How to Run (For Users)

Choose the method that best fits your needs.

### Method 1: Linux Service Installation (Recommended for Servers)

This is the most robust method for running the agent 24/7 on a production Linux server.

#### Part 1: Run the Installer

Execute the appropriate command on your server.

  * **For a public GitHub repository:**
    ```bash
    curl -sSL https://raw.githubusercontent.com/your-github-username/your-repo-name/main/install.sh | sudo bash
    ```
  * **For a private GitHub repository:**
    This command will securely prompt you for a GitHub Personal Access Token.
    ```bash
    read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN && \
    curl -sSL -H "Authorization: token $GITHUB_TOKEN" \
    https://raw.githubusercontent.com/theeghanprojecthub/event-listener-demo/main/install.sh | sudo -E bash
    ```

#### Part 2: Post-Installation Configuration and Usage

After the installation script finishes, the agent is running with default settings. Follow these steps to configure and validate it.

1.  **Verify the Service is Running**
    First, check the status of the newly installed service to make sure it's active.

    ```bash
    sudo systemctl status log-agent.service
    ```

    You should see output that includes a line like `Active: active (running)`.

2.  **Configure Your Sources and Destinations**
    The agent is now using the default rules. Use the `log-agent-ctl` tool to customize your setup.

      * **Clear the default rules:** It's good practice to start with a clean slate.
        ```bash
        sudo log-agent-ctl clear-sources
        sudo log-agent-ctl clear-destinations
        ```
      * **Add a source to monitor:** This example adds the main system log.
        ```bash
        sudo log-agent-ctl add-source main_syslog /var/log/syslog MODIFY
        ```
      * **Add a destination to send logs to:** This example adds a remote syslog server.
        ```bash
        sudo log-agent-ctl add-destination-syslog central_logs logs.mycompany.com 514 your-secret-token
        ```
      * **Link the source to the destination:** This tells the agent to send logs from `main_syslog` to `central_logs`.
        ```bash
        sudo log-agent-ctl link-source main_syslog central_logs
        ```
      * **View your final configuration:**
        ```bash
        log-agent-ctl show-config
        ```

3.  **Test the Agent**
    Now you can generate some log data to see if it's being forwarded correctly.

      * **Watch the agent's live logs in one terminal:**
        ```bash
        sudo journalctl -u log-agent.service -f
        ```
      * **In a second terminal, create a test log entry:**
        This command appends a line to the source file you configured.
        ```bash
        echo "This is a test log from my server - $(date)" | sudo tee -a /var/log/syslog
        ```

4.  **Validate in Your Destination**
    Finally, go to your remote syslog's "Events" or "Logs" dashboard. You should see the test log message appear in real-time, confirming the entire pipeline is working.

5.  **Uninstalling the Agent**
    If you need to completely remove the agent and all its configurations, use the built-in uninstall command.

    ```bash
    sudo log-agent-ctl uninstall
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

This repository uses **GitHub Actions** to automate the release process. When a new version tag (e.g., `v1.0.1`) is pushed, a workflow is triggered. This workflow uses **PyInstaller** to compile the `agent.py` script and its dependencies into a single, dependency-free binary. It then creates a new **GitHub Release** and uploads the compiled binary along with the default configuration files as release assets. This automated process makes new versions of the agent immediately available for the Linux service installation method.