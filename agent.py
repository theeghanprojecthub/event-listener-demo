import os
import time
import json
import logging
import sys
import socket
import requests
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(message)s",
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


def forward_logs(new_data, destination_config):
    """
    Forwards new log data to a single configured destination.
    """
    dest_type = destination_config.get("type")
    dest_id = destination_config.get("id", "N/A")

    if dest_type == "file":
        try:
            with open(destination_config["path"], "ab") as dest:
                dest.write(new_data)
            logging.info(f"Forwarded {len(new_data)} bytes to file: {dest_id}.")
        except IOError as e:
            logging.error(f"File IO error for {dest_id}: {e}")

    elif dest_type == "syslog":
        host = destination_config.get("host")
        port = destination_config.get("port")
        token = destination_config.get("token")
        if not all([host, port]):
            logging.error(f"Syslog destination {dest_id} requires 'host' and 'port'.")
            return
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
            logging.info(f"Forwarded {len(new_data)} bytes to syslog: {dest_id}.")
        except socket.error as e:
            logging.error(f"Socket error for syslog {dest_id}: {e}")

    elif dest_type == "http":
        url = destination_config.get("url")
        token = destination_config.get("token")
        if not url:
            logging.error(f"HTTP destination {dest_id} requires a 'url'.")
            return
        try:
            headers = {"Content-Type": "application/octet-stream"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = requests.post(url, data=new_data, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Forwarded {len(new_data)} bytes to HTTP: {dest_id}.")
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP request error for {dest_id}: {e}")

    else:
        logging.error(f"Unknown destination type for {dest_id}: '{dest_type}'")


def route_and_forward(new_data, source_id, all_destinations):
    """
    Finds matching destinations for a given source and forwards the data.
    """
    for dest in all_destinations:
        source_ids = dest.get("source_ids", [])
        if "*" in source_ids or source_id in source_ids:
            forward_logs(new_data, dest)


def monitor_source(source_config, all_destinations):
    """
    The main monitoring loop for a single source file.
    This function runs in its own thread.
    """
    source_path = source_config.get("path")
    source_id = source_config.get("id")
    enabled_events = set(source_config.get("enabled_events", []))

    if not all([source_path, source_id]):
        logging.error(f"Source config is missing 'path' or 'id': {source_config}")
        return

    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    last_known_state = {"exists": False, "size": 0}

    while True:
        try:
            time.sleep(2)
            file_exists = os.path.exists(source_path)

            if file_exists and not last_known_state["exists"]:
                if "CREATE" in enabled_events:
                    logging.info(f"CREATE event on '{source_id}'.")
                last_known_state = {"exists": True, "size": 0}

            elif not file_exists and last_known_state["exists"]:
                if "DELETE" in enabled_events:
                    logging.info(f"DELETE event on '{source_id}'.")
                last_known_state = {"exists": False, "size": 0}

            elif file_exists:
                current_size = os.path.getsize(source_path)
                if current_size > last_known_state["size"]:
                    if "MODIFY" in enabled_events:
                        with open(source_path, "rb") as src:
                            src.seek(last_known_state["size"])
                            new_data = src.read()
                            if new_data:
                                route_and_forward(new_data, source_id, all_destinations)
                    last_known_state["size"] = current_size
                elif current_size < last_known_state["size"]:
                    if "MODIFY" in enabled_events:
                        logging.warning(f"File truncated on '{source_id}'. Resetting.")
                        with open(source_path, "rb") as src:
                            new_data = src.read()
                            if new_data:
                                route_and_forward(new_data, source_id, all_destinations)
                    last_known_state["size"] = current_size
        except Exception as e:
            logging.error(f"Error in monitor thread for '{source_id}': {e}")


def main():
    """
    The main entry point that starts a monitoring thread for each source.
    """
    monitor_config = load_json_config("monitor_rules.json")
    action_config = load_json_config("action_rules.json")

    source_configs = monitor_config.get("sources", [])
    destination_configs = action_config.get("destinations", [])

    if not source_configs:
        logging.error("No sources defined in monitor_rules.json. Exiting.")
        sys.exit(1)

    for config in destination_configs:
        if config.get("type") == "file":
            os.makedirs(os.path.dirname(config["path"]), exist_ok=True)

    logging.info(f"--- Starting agent with {len(source_configs)} monitor(s) ---")

    threads = []
    for source_config in source_configs:
        thread = Thread(
            target=monitor_source,
            args=(source_config, destination_configs),
            name=source_config.get("id"),
        )
        threads.append(thread)
        thread.daemon = True
        thread.start()

    try:
        # Keep the main thread alive to allow daemon threads to run
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\n--- Agent stopped by user. ---")


if __name__ == "__main__":
    main()
