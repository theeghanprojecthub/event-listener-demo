import time
import random
import datetime
import os


def generate_log_line():
    """
    Creates a single, randomized log line with a realistic format.
    """
    log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
    servers = ["web-01", "db-01", "api-03", "cache-main", "worker-05"]
    messages = [
        "User authentication successful",
        "Failed to connect to database: timeout",
        "Request processed in 25ms",
        "Cache miss for key 'user:123'",
        "Starting background job: process_payments",
        "Disk space is critically low on /var/log",
        "New user signed up: test@example.com",
    ]

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    level = random.choice(log_levels)
    server = random.choice(servers)
    message = random.choice(messages)

    return f"[{timestamp}] [{level}] [{server}] - {message}\n"


def main():
    """
    Continuously generates log lines and appends them to the source log file.
    """
    target_file = "source_logs/systemlogs.log"

    # Ensure the directory exists
    os.makedirs(os.path.dirname(target_file), exist_ok=True)

    print(f"--- Starting Log Generator ---")
    print(f"Appending logs to: {target_file}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            log_line = generate_log_line()
            with open(target_file, "a") as f:
                f.write(log_line)

            print(f"Generated: {log_line.strip()}")

            # Wait for a random interval to simulate real-world traffic
            time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        print("\n--- Log Generator stopped. ---")
    except IOError as e:
        print(f"\nError writing to log file: {e}")


if __name__ == "__main__":
    main()
