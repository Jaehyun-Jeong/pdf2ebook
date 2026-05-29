#!/usr/bin/env bash
# Ralph Loop driver. Re-invokes claude -p headlessly until stopped.
# Usage: ./loop.sh [max_iterations]   (0 or omitted = unlimited)

set -u
max="${1:-0}"   # 0 = unlimited
n=0

while :; do
  n=$((n+1))
  if [ "$max" -gt 0 ] && [ "$n" -gt "$max" ]; then
    echo "Reached max iterations ($max). Stopping."
    break
  fi
  echo "=== Ralph iteration $n  $(date -Iseconds) ==="
  cat PROMPT.md | claude -p --dangerously-skip-permissions
  if [ $? -ne 0 ]; then
    echo "claude exited non-zero; stopping."
    break
  fi
  sleep 2
done
