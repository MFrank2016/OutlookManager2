#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env.compose.local"

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "缺少命令: $command_name" >&2
    exit 1
  fi
}

wait_for_url() {
  local url="$1"
  local service_name="$2"
  local max_attempts=10
  local sleep_seconds=1
  local attempt

  for ((attempt = 1; attempt <= max_attempts; attempt++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi

    if (( attempt < max_attempts )); then
      sleep "$sleep_seconds"
    fi
  done

  echo "探活失败: ${service_name} (${url})" >&2
  return 1
}

require_command docker
require_command curl

if [[ ! -f "$ENV_FILE" ]]; then
  echo "缺少 .env.compose.local，请先执行：" >&2
  echo "cp .env.compose.example .env.compose.local" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${PORT:?PORT is required in .env.compose.local}"
: "${FRONTEND_PORT:?FRONTEND_PORT is required in .env.compose.local}"
: "${POSTGRES_PORT:?POSTGRES_PORT is required in .env.compose.local}"

cd "$REPO_ROOT"

docker compose --env-file .env.compose.local up -d --build
docker compose ps
wait_for_url "http://127.0.0.1:${PORT}/healthz" "API /healthz"
wait_for_url "http://127.0.0.1:${FRONTEND_PORT}" "Frontend 首页"

echo
echo "✅ 本地 Compose 栈已启动"
echo "- Frontend: http://127.0.0.1:${FRONTEND_PORT}"
echo "- API: http://127.0.0.1:${PORT}"
echo "- PostgreSQL: 127.0.0.1:${POSTGRES_PORT}"
echo
echo "常用日志命令："
echo "- docker compose logs -f outlook-email-api"
echo "- docker compose logs -f outlook-email-frontend"
echo "- docker compose logs -f postgresql"
