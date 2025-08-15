#!/bin/bash

cd "$(dirname "$0")"

PID_FILE="agent.pid"
LOG_FILE="agent_local.log"
PYTHON_CMD="python"
AGENT_SCRIPT="agent.py"

start() {
    echo ">>> Starting Log Forwarding Agent locally... 🚀"

    if [ -f "$PID_FILE" ]; then
        echo "Agent is already running (PID file exists). Use 'restart' or 'stop' first."
        exit 1
    fi

    mkdir -p source_logs
    mkdir -p destination_logs

    nohup $PYTHON_CMD -u $AGENT_SCRIPT > "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"

    sleep 1

    if ps -p $(cat $PID_FILE) > /dev/null; then
        echo "Agent started successfully with PID $(cat $PID_FILE)."
        echo "View logs with: ./run_local.sh logs"
    else
        echo "Failed to start the agent. Check '$LOG_FILE' for errors."
        rm "$PID_FILE"
        exit 1
    fi
}

stop() {
    echo ">>> Stopping Log Forwarding Agent... 🛑"

    if [ ! -f "$PID_FILE" ]; then
        echo "Agent is not running (no PID file found)."
        return
    fi

    PID=$(cat $PID_FILE)

    kill "$PID"

    sleep 1

    if ps -p "$PID" > /dev/null; then
        echo "Failed to stop the agent gracefully. Forcing..."
        kill -9 "$PID"
    fi

    rm "$PID_FILE"
    echo "Agent has been stopped."
}

logs() {
    echo ">>> Following local agent logs... (Press Ctrl+C to exit)"
    tail -f "$LOG_FILE"
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p "$PID" > /dev/null; then
            echo "Agent is RUNNING with PID $PID."
        else
            echo "Agent is STOPPED (stale PID file found)."
        fi
    else
        echo "Agent is STOPPED."
    fi
}

restart() {
    echo ">>> Restarting Log Forwarding Agent..."
    stop
    start
}

usage() {
    echo "Usage: $0 {start|stop|restart|status|logs}"
    echo
    echo "Commands:"
    echo "  start    : Starts the agent as a background process."
    echo "  stop     : Stops the background agent process."
    echo "  restart  : Restarts the agent."
    echo "  status   : Checks if the agent is running."
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
    status)
        status
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
