import os
import time
import json
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)


def get_path_details(path):
    """Returns a tuple of (modification_time, is_directory)."""
    return os.path.getmtime(path), os.path.isdir(path)


def main():
    """
    A robust polling monitor that correctly identifies files and directories.
    It reads its configuration from rules.json and does not depend on any
    third-party libraries.
    """
    try:
        with open("rules.json", "r") as f:
            rule = json.load(f)["rules"][0]
            path_to_watch = rule["path"]
    except (FileNotFoundError, IndexError):
        logging.error("Could not read path from rules.json. Exiting.")
        sys.exit(1)

    if not os.path.exists(path_to_watch):
        logging.warning(f"Path '{path_to_watch}' does not exist. Creating it.")
        os.makedirs(path_to_watch)

    logging.info(
        f"--- Starting robust polling monitor on: {os.path.abspath(path_to_watch)} ---"
    )

    state_before = {
        name: get_path_details(os.path.join(path_to_watch, name))
        for name in os.listdir(path_to_watch)
    }

    try:
        while True:
            time.sleep(2)

            state_after = {
                name: get_path_details(os.path.join(path_to_watch, name))
                for name in os.listdir(path_to_watch)
            }

            added = set(state_after) - set(state_before)
            removed = set(state_before) - set(state_after)

            for name in set(state_before) & set(state_after):
                if state_before[name][0] != state_after[name][0]:
                    metadata = {
                        "event_type": "MODIFY",
                        "is_directory": state_after[name][1],
                        "source_path": os.path.join(path_to_watch, name),
                    }
                    logging.info(json.dumps(metadata))

            if added:
                for name in added:
                    metadata = {
                        "event_type": "CREATE",
                        "is_directory": state_after[name][1],
                        "source_path": os.path.join(path_to_watch, name),
                    }
                    logging.info(json.dumps(metadata))

            if removed:
                for name in removed:
                    metadata = {
                        "event_type": "DELETE",
                        "is_directory": state_before[name][1],
                        "source_path": os.path.join(path_to_watch, name),
                    }
                    logging.info(json.dumps(metadata))

            state_before = state_after

    except KeyboardInterrupt:
        logging.info("\n--- Monitor stopped. ---")


if __name__ == "__main__":
    main()
