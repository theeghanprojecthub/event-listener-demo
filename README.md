# Real-Time Log Forwarding Agent

This project is a robust, policy-based log forwarding agent designed for maximum flexibility. It uses a custom Python script to "tail" a source log file in real-time and forward new data to multiple destinations simultaneously, including local files, remote syslog servers, and HTTP endpoints.

The agent can be run in multiple ways: as a simple local script, as a portable Docker container, or as a professional, auto-restarting service on a production Linux server.

-----

## Features

  * **Multi-Destination Forwarding:** Send logs to any combination of local files, remote syslog servers, and HTTP endpoints at the same time.
  * **Authentication Support:** Natively supports token-based authentication for both syslog (token-in-message) and HTTP (Bearer token) destinations.
  * **Rule-Based Configuration:** Uses simple JSON files to define the source file (`monitor_rules.json`) and a list of destinations (`action_rules.json`).
  * **Multiple Execution Modes:** Can be run directly with Python, as a local background script, via Docker, or as a robust `systemd` service.
  * **Automated Releases:** New versions are automatically built into a single binary using PyInstaller and published to GitHub Releases via GitHub Actions.
  * **Professional Installation:** A one-line installation script (`install.sh`) sets up the agent as a secure, managed `systemd` service on Linux.
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
└── requirements.txt           # Build-time dependencies (PyInstaller, requests)
```

-----

## How to Run (For Users)

Choose the method that best fits your needs.

### Method 1: Linux Service Installation (Recommended for Servers)

This is the most robust method for running the agent 24/7 on a production Linux server. It installs the agent as a system service that starts on boot and restarts automatically.

1.  **Run the Installer:**
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

   2.  **Manage the Agent:**
       Congratulations, the installation was successfully! The agent is now running as a background service on your Kali machine.
       The final output of the installer script tells you everything you need to know. Here are the immediate next steps to take.
       After installation, you can manage the agent using the new `log-agent-ctl` command.

         * **Get Help:**
           ```bash
           log-agent-ctl help
           ```
         * **View Current Configuration:**
           ```bash
           log-agent-ctl show-config
           ```
         * **Add a new destination (e.g., an HTTP endpoint):**
           ```bash
           sudo log-agent-ctl add-destination-http https://your-endpoint.com/logs your-secret-token
           ```

-----

### Next Steps

#### 1\. Verify the Service is Running

First, check the status of the newly installed service to make sure it's active.

```bash
sudo systemctl status log-agent.service
```

You should see output that includes a line like `Active: active (running)`.

#### 2\. Configure Your Destinations rules

Right now, the agent is using the default rules. You need to tell it where to send the logs. Use the `log-agent-ctl` tool to add your syslog destinations.

  * **First, clear the default destinations:**

    ```bash
    sudo log-agent-ctl clear-destinations
    ```

    * **Next, add your HTTP destination:**

      ```bash
      sudo log-agent-ctl add-destination-http https://logs.collector.com/v1/logs/bulk token22442223
      ```

    * **(Optional) Add your Syslog destination:**
      If you want to send to both, you can also add the syslog endpoint.

      ```bash
      sudo log-agent-ctl add-destination-syslog syslog.collector.com 514 token22442223
      ```

#### 3\. Test the Agent

Now you can generate some log data to see if it's being forwarded correctly.

  * **Watch the agent's live logs in one terminal:**

    ```bash
    sudo journalctl -u log-agent.service -f
    ```

    * **In a second terminal, create a test log entry:**
      The agent is watching the `/var/log/source_logs/systemlogs.log` file.

      ```bash
      echo "This is a test log from my Kali machine - $(date)" | sudo tee -a /var/log/source_logs/systemlogs.log
      ```

#### 4\. Validate in Destination syslog

Finally, go to your Syslog "Events" or "Logs" dashboard. You should see the test log message appear in real-time.

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

This repository uses **GitHub Actions** to automate the release process. When a new version tag (e.g., `v1.0.1`) is pushed, 
a workflow is triggered. This workflow uses **PyInstaller** to compile the `agent.py` script and its dependencies into a single,
dependency-free binary. It then creates a new **GitHub Release** and uploads the compiled binary along with the default configuration
files as release assets. This automated process makes new versions of the agent immediately available for the Linux service installation
method.