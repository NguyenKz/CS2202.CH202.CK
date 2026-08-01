#!/usr/bin/env bash
# Run plausibility demo: http://127.0.0.1:8000
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
DOAN_DIR="$(cd "$DEMO_DIR/.." && pwd)"
REPO_DIR="$(cd "$DOAN_DIR/.." && pwd)"
PORT="${PORT:-8000}"

# Prefer local venv: doan/.venv → repo/venv → already-active python
if [[ -f "$DOAN_DIR/.venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$DOAN_DIR/.venv/bin/activate"
elif [[ -f "$REPO_DIR/venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source "$REPO_DIR/venv/bin/activate"
elif [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "Không tìm thấy venv. Tạo rồi cài deps:"
  echo "  python3 -m venv \"$REPO_DIR/venv\""
  echo "  source \"$REPO_DIR/venv/bin/activate\""
  echo "  pip install -r \"$DOAN_DIR/requirements-eval.txt\""
  exit 1
fi

if [[ ! -f "$DOAN_DIR/.env" ]]; then
  echo "Thiếu $DOAN_DIR/.env — thêm OPENAI_API_KEY=sk-..."
  exit 1
fi

if ! python -c "import fastapi, uvicorn, openai" 2>/dev/null; then
  echo "Thiếu dependency — đang cài từ requirements-eval.txt ..."
  python -m pip install -r "$DOAN_DIR/requirements-eval.txt"
fi

echo "Demo: http://127.0.0.1:${PORT}"
echo "Ctrl+C để dừng."
cd "$DEMO_DIR"
exec env PORT="$PORT" python app.py
