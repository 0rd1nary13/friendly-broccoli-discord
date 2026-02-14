#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="${ROOT_DIR}/var/run"
LOG_DIR="${ROOT_DIR}/var/log"
PID_FILE="${PID_DIR}/relay.pid"
LOG_FILE="${LOG_DIR}/relay.log"
COMMAND="uv run python -m goob_ai.main"

ensure_dirs() {
  mkdir -p "${PID_DIR}" "${LOG_DIR}"
}

is_running() {
  if [[ ! -f "${PID_FILE}" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "${PID_FILE}")"
  if [[ -z "${pid}" ]]; then
    return 1
  fi

  if kill -0 "${pid}" >/dev/null 2>&1; then
    return 0
  fi

  rm -f "${PID_FILE}"
  return 1
}

start() {
  ensure_dirs
  if is_running; then
    echo "Relay is already running (PID $(cat "${PID_FILE}"))."
    return 0
  fi

  cd "${ROOT_DIR}"
  nohup ${COMMAND} >>"${LOG_FILE}" 2>&1 &
  echo $! >"${PID_FILE}"
  sleep 1

  if is_running; then
    echo "Relay started (PID $(cat "${PID_FILE}"))."
    echo "Logs: ${LOG_FILE}"
    return 0
  fi

  echo "Relay failed to start. Check logs: ${LOG_FILE}"
  return 1
}

stop() {
  if ! is_running; then
    echo "Relay is not running."
    return 0
  fi

  local pid
  pid="$(cat "${PID_FILE}")"
  kill "${pid}" >/dev/null 2>&1 || true
  sleep 1

  if kill -0 "${pid}" >/dev/null 2>&1; then
    echo "Process did not exit gracefully; sending SIGKILL."
    kill -9 "${pid}" >/dev/null 2>&1 || true
  fi

  rm -f "${PID_FILE}"
  echo "Relay stopped."
}

status() {
  if is_running; then
    echo "Relay is running (PID $(cat "${PID_FILE}"))."
  else
    echo "Relay is not running."
  fi
}

logs() {
  ensure_dirs
  touch "${LOG_FILE}"
  tail -f "${LOG_FILE}"
}

restart() {
  stop
  start
}

usage() {
  echo "Usage: ./scripts/relayctl.sh {start|stop|restart|status|logs}"
}

main() {
  if [[ $# -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    logs) logs ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
