#!/usr/bin/env bash
# Start local Gemma 4 12B (Unsloth UD-Q4_K_XL) via llama-server — no re-download.
# Usage:
#   ./scripts/serve_gemma.sh
#   ./scripts/serve_gemma.sh --fg          # foreground
# Env overrides: PORT, CTX, NGL, GGUF, ALIAS

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8080}"
CTX="${CTX:-4096}"
NGL="${NGL:-999}"
ALIAS="${ALIAS:-gemma-4-12b}"
LOG="${LOG:-/tmp/gemma4-llama-server.log}"
PIDFILE="${PIDFILE:-/tmp/gemma4-llama-server.pid}"

GGUF="${GGUF:-/Users/nguyenkz/Documents/code/LocalLLM/models/cache/hub/models--unsloth--gemma-4-12b-it-GGUF/snapshots/d997c805aafe035a8024f961c6e1afd6b30d79a5/gemma-4-12b-it-UD-Q4_K_XL.gguf}"

if [[ ! -e "$GGUF" ]]; then
  echo "ERROR: GGUF not found: $GGUF" >&2
  echo "Expected LocalLLM cache (unsloth gemma-4-12b-it UD-Q4_K_XL)." >&2
  exit 1
fi

LLAMA_SERVER="${LLAMA_SERVER:-$(command -v llama-server || true)}"
if [[ -z "$LLAMA_SERVER" ]]; then
  echo "ERROR: llama-server not found (brew install llama.cpp)" >&2
  exit 1
fi

if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Already listening on :$PORT — skip start."
  echo "API: http://127.0.0.1:${PORT}/v1"
  exit 0
fi

echo "Starting Gemma from local GGUF (no download)..."
echo "  $GGUF"
echo "  alias=$ALIAS port=$PORT ctx=$CTX ngl=$NGL"

FG=0
[[ "${1:-}" == "--fg" ]] && FG=1

CMD=(
  "$LLAMA_SERVER"
  -m "$GGUF"
  --alias "$ALIAS"
  --host 127.0.0.1
  --port "$PORT"
  -c "$CTX"
  -ngl "$NGL"
  --jinja
)

if [[ "$FG" -eq 1 ]]; then
  exec "${CMD[@]}"
fi

nohup "${CMD[@]}" >"$LOG" 2>&1 &
echo $! >"$PIDFILE"
echo "PID $(cat "$PIDFILE")  log=$LOG"

# Wait until API is up
for i in $(seq 1 90); do
  if curl -sf "http://127.0.0.1:${PORT}/v1/models" >/dev/null 2>&1; then
    echo "Ready: http://127.0.0.1:${PORT}/v1"
    echo "Eval tip:"
    echo "  python scripts/run_gemma_eval.py --mode ORIG"
    exit 0
  fi
  sleep 2
done

echo "WARN: server started but /v1/models not ready yet — check $LOG" >&2
exit 1
