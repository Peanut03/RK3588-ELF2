#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

VOICE_SERVICE="voice_service.py"
AI_ASSISTANT="ai_assistant_main.py"

LOG_DIR="${SCRIPT_DIR}/logs"
PID_DIR="${SCRIPT_DIR}/pids"

VOICE_SERVICE_LOG="${LOG_DIR}/voice_service.log"
AI_ASSISTANT_LOG="${LOG_DIR}/ai_assistant.log"

VOICE_SERVICE_PID="${PID_DIR}/voice_service.pid"
AI_ASSISTANT_PID="${PID_DIR}/ai_assistant.pid"

create_dirs() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
}

check_pid() {
    [ -e "$1" ] && ps -p "$(cat "$1")" > /dev/null 2>&1
}

start() {
    cd "$SCRIPT_DIR" || exit 1

    if ! check_pid "$VOICE_SERVICE_PID"; then
        nohup python3 "$VOICE_SERVICE" > "$VOICE_SERVICE_LOG" 2>&1 &
        echo $! > "$VOICE_SERVICE_PID"
        sleep 2
        if ! check_pid "$VOICE_SERVICE_PID"; then
            rm -f "$VOICE_SERVICE_PID"
        fi
    fi

    if ! check_pid "$AI_ASSISTANT_PID"; then
        nohup python3 "$AI_ASSISTANT" > "$AI_ASSISTANT_LOG" 2>&1 &
        echo $! > "$AI_ASSISTANT_PID"
        sleep 2
        if ! check_pid "$AI_ASSISTANT_PID"; then
            rm -f "$AI_ASSISTANT_PID"
        fi
    fi
}

stop() {
    if check_pid "$VOICE_SERVICE_PID"; then
        kill -15 "$(cat "$VOICE_SERVICE_PID")"
        rm -f "$VOICE_SERVICE_PID"
    else
        rm -f "$VOICE_SERVICE_PID" 
    fi

    if check_pid "$AI_ASSISTANT_PID"; then
        kill -15 "$(cat "$AI_ASSISTANT_PID")"
        rm -f "$AI_ASSISTANT_PID"
    else
        rm -f "$AI_ASSISTANT_PID" 
    fi
}

status() {
    if check_pid "$VOICE_SERVICE_PID"; then
        :
    else
        :
    fi

    if check_pid "$AI_ASSISTANT_PID"; then
        :
    else
        :
    fi
}

create_dirs

COMMAND=$1
if [ -z "$COMMAND" ]; then
    COMMAND="start"
fi

case "$COMMAND" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        status
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    *)
        exit 1
        ;;
esac

exit 0 