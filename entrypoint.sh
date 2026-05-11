#!/usr/bin/env sh
set -eu

: "${PORT:=8080}"
: "${HOME:=/data}"
: "${KIROPROXY_USER:=kiroproxy}"
: "${KIROPROXY_GROUP:=kiroproxy}"

prepare_home() {
  mkdir -p "$HOME/.kiro-proxy" "$HOME/.aws/sso/cache"
  if [ "$(id -u)" = "0" ]; then
    chown -R "$KIROPROXY_USER:$KIROPROXY_GROUP" "$HOME"
  fi
}

run_as_kiroproxy() {
  if [ "$(id -u)" = "0" ]; then
    exec gosu "$KIROPROXY_USER:$KIROPROXY_GROUP" "$@"
  fi
  exec "$@"
}

prepare_home

if [ "${1:-}" = "serve" ]; then
  run_as_kiroproxy python /app/run.py serve -p "$PORT"
fi

run_as_kiroproxy "$@"
