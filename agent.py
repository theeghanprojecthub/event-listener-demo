import os
import time
import json
import logging
import sys
import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def load_json_config(filepath):
    """
    Loads a JSON configuration file and returns its content.
    Exits the program if the file is not found or is invalid.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading config file {filepath}: {e}")
        sys.exit(1)


def forward_new_logs(source_path, destination_path, last_known_size):
    """
    Reads new data from the source, enriches it with a signature,
    and appends it to the destination file.
    """
    try:
        with open(source_path, "rb") as src, open(destination_path, "ab") as dest:
            src.seek(last_known_size)
            new_data = src.read()
            if new_data:
                # Decode to process line by line
                new_logs_str = new_data.decode("utf-8", errors="ignore")

                for line in new_logs_str.strip().split("\n"):
                    if not line:
                        continue  # Skip empty lines

                    # Add the agent's signature
                    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    enriched_line = f"[FORWARDED by Agent at {timestamp}] {line}\n"

                    dest.write(enriched_line.encode("utf-8"))

                logging.info(f"Forwarded {len(new_data)} bytes of new log data.")

    except IOError as e:
        logging.error(f"File IO error during log forwarding: {e}")


def main():
    """
    The main entry point for the log monitoring and forwarding agent.
    """
    monitor_config = load_json_config("monitor_rules.json")
    action_config = load_json_config("action_rules.json")

    source_path = monitor_config.get("source_path")
    enabled_events = set(monitor_config.get("enabled_events", []))
    destination_path = action_config.get("destination_path")

    if not all([source_path, destination_path]):
        logging.error("Source and destination paths must be defined in rule files.")
        sys.exit(1)

    os.makedirs(os.path.dirname(source_path), exist_ok=True)
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    logging.info(f"--- Starting agent ---")
    logging.info(f"Monitoring source file: {source_path}")
    logging.info(f"Forwarding to destination: {destination_path}")
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
                        forward_new_logs(
                            source_path, destination_path, last_known_state["size"]
                        )
                    last_known_state["size"] = current_size

                elif current_size < last_known_state["size"]:
                    if "MODIFY" in enabled_events:
                        logging.warning(
                            f"Source file '{source_path}' was truncated. Resetting monitor."
                        )
                        forward_new_logs(source_path, destination_path, 0)
                    last_known_state["size"] = current_size

    except KeyboardInterrupt:
        logging.info("\n--- Agent stopped by user. ---")


if __name__ == "__main__":
    main()
