#!/bin/bash
# A management script for the log forwarding agent.

cd "$(dirname "$0")"

start() {
    echo ">>> Starting Log Forwarding Agent... 🚀"
    # Create both directories on the host machine.
    mkdir -p source_logs
    mkdir -p destination_logs
    docker-compose up -d --build
    echo ">>> Agent is running in the background."
}

stop() {
    echo ">>> Stopping Log Forwarding Agent... 🛑"
    docker-compose down
    echo ">>> Agent has been stopped."
}

logs() {
    echo ">>> Following logs... (Press Ctrl+C to exit)"
    docker-compose logs -f
}

restart() {
    echo ">>> Restarting Log Forwarding Agent..."
    stop
    start
}

usage() {
    echo "Usage: $0 {start|stop|restart|logs}"
    echo
    echo "Commands:"
    echo "  start    : Builds and starts the agent in the background."
    echo "  stop     : Stops and removes the agent's container."
    echo "  restart  : Restarts the agent."
    echo "  logs     : Shows the live logs from the agent."
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit 0