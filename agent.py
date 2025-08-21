import os
import time
import json
import logging
import sys
import socket
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def load_json_config(filepath):
    """
    Loads a JSON configuration file and returns its content.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading config file {filepath}: {e}")
        sys.exit(1)


def forward_logs(new_data, destination_configs):
    """
    Forwards new log data to all configured destinations.
    """
    for config in destination_configs:
        dest_type = config.get("type")

        if dest_type == "file":
            try:
                with open(config["path"], "ab") as dest:
                    dest.write(new_data)
                logging.info(
                    f"Forwarded {len(new_data)} bytes to file: {config['path']}."
                )
            except IOError as e:
                logging.error(f"File IO error for {config['path']}: {e}")

        elif dest_type == "syslog":
            host = config.get("host")
            port = config.get("port")
            token = config.get("token")
            if not all([host, port]):
                logging.error("Syslog destination requires 'host' and 'port'.")
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    for line in new_data.strip().split(b"\n"):
                        if not line:
                            continue

                        message = (
                            f"{token} {line.decode('utf-8')}\n".encode("utf-8")
                            if token
                            else line
                        )
                        sock.sendto(message, (host, port))
                logging.info(
                    f"Forwarded {len(new_data)} bytes to syslog server {host}:{port}."
                )
            except socket.error as e:
                logging.error(f"Socket error sending to syslog {host}:{port}: {e}")

        elif dest_type == "http":
            url = config.get("url")
            token = config.get("token")
            if not url:
                logging.error("HTTP destination requires a 'url'.")
                continue
            try:
                headers = {"Content-Type": "application/octet-stream"}
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                response = requests.post(
                    url, data=new_data, headers=headers, timeout=10
                )
                response.raise_for_status()
                logging.info(
                    f"Forwarded {len(new_data)} bytes to HTTP endpoint: {url}."
                )
            except requests.exceptions.RequestException as e:
                logging.error(f"HTTP request error for {url}: {e}")

        else:
            logging.error(f"Unknown destination type: '{dest_type}'")


def main():
    """
    The main entry point for the log monitoring and forwarding agent.
    """
    monitor_config = load_json_config("monitor_rules.json")
    action_config = load_json_config("action_rules.json")

    source_path = monitor_config.get("source_path")
    enabled_events = set(monitor_config.get("enabled_events", []))
    destination_configs = action_config.get("destinations", [])

    if not all([source_path, destination_configs]):
        logging.error("Source path and at least one destination must be defined.")
        sys.exit(1)

    os.makedirs(os.path.dirname(source_path), exist_ok=True)

    for config in destination_configs:
        if config.get("type") == "file":
            os.makedirs(os.path.dirname(config["path"]), exist_ok=True)

    logging.info(f"--- Starting agent ---")
    logging.info(f"Monitoring source file: {source_path}")
    logging.info(f"Forwarding to {len(destination_configs)} destination(s).")
    logging.info(f"Enabled events: {list(enabled_events)}")

    last_known_state = {"exists": False, "size": 0}

    try:
        while True:
            time.sleep(2)

            file_exists = os.path.exists(source_path)

            if file_exists and not last_known_state["exists"]:
                if "CREATE" in enabled_events:
                    logging.info(f"CREATE event: Source file '{source_path}' appeared.")
                last_known_state = {"exists": True, "size": 0}

            elif not file_exists and last_known_state["exists"]:
                if "DELETE" in enabled_events:
                    logging.info(
                        f"DELETE event: Source file '{source_path}' was removed."
                    )
                last_known_state = {"exists": False, "size": 0}

            elif file_exists:
                current_size = os.path.getsize(source_path)

                if current_size > last_known_state["size"]:
                    if "MODIFY" in enabled_events:
                        with open(source_path, "rb") as src:
                            src.seek(last_known_state["size"])
                            new_data = src.read()
                            if new_data:
                                forward_logs(new_data, destination_configs)
                    last_known_state["size"] = current_size

                elif current_size < last_known_state["size"]:
                    if "MODIFY" in enabled_events:
                        logging.warning(
                            f"Source file '{source_path}' was truncated. Resetting monitor."
                        )
                        with open(source_path, "rb") as src:
                            new_data = src.read()
                            if new_data:
                                forward_logs(new_data, destination_configs)
                    last_known_state["size"] = current_size

    except KeyboardInterrupt:
        logging.info("\n--- Agent stopped by user. ---")


if __name__ == "__main__":
    main()
