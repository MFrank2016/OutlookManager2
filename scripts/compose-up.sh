#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env.compose.local"
USE_BUILD=1
LOGS_ON_FAIL=0

require_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "缺少命令: $command_name" >&2
    exit 1
  fi
}

read_env_value() {
  local key="$1"
  local file="$2"
  local value

  value="$(grep -E "^${key}=" "$file" | head -n 1 | cut -d'=' -f2- || true)"
  value="${value%$'\r'}"

  if [[ -z "$value" ]]; then
    echo "缺少配置: ${key} (from ${file})" >&2
    exit 1
  fi

  printf '%s\n' "$value"
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

  if (( LOGS_ON_FAIL )); then
    docker compose logs --tail=40 outlook-email-api || true
    docker compose logs --tail=40 outlook-email-frontend || true
    docker compose logs --tail=40 postgresql || true
  fi

  return 1
}

require_command docker
require_command curl

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      USE_BUILD=0
      shift
      ;;
    --logs-on-fail)
      LOGS_ON_FAIL=1
      shift
      ;;
    *)
      echo "未知参数: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "缺少 .env.compose.local，请先执行：" >&2
  echo "cp .env.compose.example .env.compose.local" >&2
  exit 1
fi

PORT="$(read_env_value "PORT" "$ENV_FILE")"
FRONTEND_PORT="$(read_env_value "FRONTEND_PORT" "$ENV_FILE")"
POSTGRES_PORT="$(read_env_value "POSTGRES_PORT" "$ENV_FILE")"

cd "$REPO_ROOT"

if (( USE_BUILD )); then
  docker compose --env-file .env.compose.local up -d --build
else
  docker compose --env-file .env.compose.local up -d
fi
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
