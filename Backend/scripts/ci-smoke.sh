#!/usr/bin/env bash
set -euo pipefail

# Start uvicorn and capture logs to a file for CI debugging
UVICORN_LOG=${UVICORN_LOG:-uvicorn.log}
UVICORN_PID_FILE=${UVICORN_PID_FILE:-uvicorn.pid}

python -m uvicorn main:app --host 127.0.0.1 --port 8001 --log-level warning > "${UVICORN_LOG}" 2>&1 & echo $! > "${UVICORN_PID_FILE}"

started=false
for i in {1..10}; do
  if curl -sSf http://127.0.0.1:8001/metrics >/dev/null 2>&1; then
    echo "metrics endpoint reachable"
    started=true
    break
  fi
  sleep 0.5
done

if [ "${started}" = "false" ]; then
  echo "ERROR: metrics endpoint not reachable after wait; dumping ${UVICORN_LOG}:"
  cat "${UVICORN_LOG}" || true
  echo "Killing uvicorn pid: $(cat ${UVICORN_PID_FILE})"
  kill $(cat "${UVICORN_PID_FILE}") || true
  exit 1
fi

# Kill server and exit success
kill $(cat "${UVICORN_PID_FILE}") || true
