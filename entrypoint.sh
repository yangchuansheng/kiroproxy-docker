#!/usr/bin/env sh
set -eu

: "${PORT:=8080}"
: "${HOME:=/data}"

mkdir -p "$HOME/.kiro-proxy" "$HOME/.aws/sso/cache"

if [ "${1:-}" = "serve" ]; then
  exec python /app/run.py serve -p "$PORT"
fi

exec "$@"
