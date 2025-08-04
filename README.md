# Real-Time Log Forwarding Agent

This project is an educational demonstration of a robust, policy-based log forwarding agent. It uses a custom Python script to "tail" a source log file in real-time, enrich the new log entries with a signature, and forward them to a destination file.

The entire system is containerized with Docker and managed by a powerful command-line script, making it easy to run and test.

## Features

  * **Real-time Log Tailing:** Continuously monitors a source file and processes new data as it's written.
  * **Content Enrichment:** Adds a timestamped signature to each forwarded log line, providing clear traceability.
  * **Rule-Based Configuration:** Uses separate, simple JSON files to define the source file (`monitor_rules.json`) and the destination file (`action_rules.json`).
  * **Zero Dependencies:** The core agent is written in pure Python with no external libraries.
  * **Dockerized:** Runs in a predictable, isolated environment using Docker and Docker Compose.
  * **Log Generation Utility:** Includes a `log_generator.py` script to simulate live log traffic for easy, real-time testing.
  * **CLI Management:** Comes with a powerful `run_monitor.sh` script to `start`, `stop`, `restart`, and view `logs`.

-----

## Project Structure

```
.
├── Dockerfile
├── agent.py
├── docker-compose.yml
├── log_generator.py
├── monitor_rules.json
├── action_rules.json
├── README.md
├── requirements.txt
├── run_monitor.sh
├── source_logs/
│   └── systemlogs.log (created by generator)
└── destination_logs/
    └── destinationlog.log (created by agent)
```

-----

## Prerequisites

Before you begin, ensure you have the following installed on your system:

  * [Docker](https://docs.docker.com/get-docker/)
  * [Docker Compose](https://docs.docker.com/compose/install/)
  * [Python 3](https://www.python.org/downloads/) (for running the log generator locally)

-----

## Setup & Usage

Follow these steps to get the agent running and see it in action.

**1. Create Project Files**

Ensure all the project files (`agent.py`, `Dockerfile`, etc.) are in the same directory on your computer.

**2. Make the Management Script Executable**
Open your terminal and run this command once:

```bash
chmod +x run_monitor.sh
```

**3. Start the Monitoring Agent**
This command will build the Docker image and start the container in the background. It also creates the necessary log directories.

```bash
./run_monitor.sh start
```

**4. Test the Real-Time Forwarding**
This process requires three separate terminal windows.

  * **Terminal 1: Watch the Agent's Logs**
    See what the agent is doing behind the scenes.

    ```bash
    ./run_monitor.sh logs
    ```

    You will see it start up and begin monitoring.

  * **Terminal 2: Start the Log Generator**
    This script will start writing new lines to `source_logs/systemlogs.log`.

    ```bash
    python log_generator.py
    ```

    You will see the randomly generated logs being printed in this terminal as they are created.

  * **Terminal 3: Validate the Destination**
    Check the contents of the destination file.

    ```bash
    # View the entire file
    cat destination_logs/destinationlog.log

    # Or tail it to see new logs as they arrive
    tail -f destination_logs/destinationlog.log
    ```

**5. Observe the Results**
In `destination_logs/destinationlog.log`, you will see output similar to this, proving the agent processed each line:

```
[FORWARDED by Agent at 2025-08-04T17:30:15.123456+00:00] [2025-08-04 17:30:14] [ERROR] [db-01] - Failed to connect to database: timeout
[FORWARDED by Agent at 2025-08-04T17:30:17.654321+00:00] [2025-08-04 17:30:16] [INFO] [web-01] - Request processed in 25ms
```

**6. Stop Everything**

  * In Terminal 2, press `Ctrl+C` to stop the log generator.
  * To stop the agent's Docker container, run:
    ```bash
    ./run_monitor.sh stop
    ```

-----

## How It Works

  * **`agent.py`**: A dependency-free Python script that runs in an infinite loop. It periodically checks the size of the source file defined in `monitor_rules.json`. When the size increases, it reads only the new data, prepends a signature, and appends it to the destination file defined in `action_rules.json`.
  * **`log_generator.py`**: A simple utility to simulate a real application writing to a log file, allowing you to test the agent's real-time capabilities.
  * **`monitor_rules.json` & `action_rules.json`**: These configurations file decouple the agent's logic from its configuration, allowing you to easily change the source and destination paths without modifying the code.
  * **`run_monitor.sh`**: A command-line interface that simplifies managing the Docker Compose application lifecycle.
  * **`Dockerfile` & `docker-compose.yml`**: These files define how to build the container image for the agent and how to run it, including the crucial volume mappings that link the directories on your computer to the directories inside the container.