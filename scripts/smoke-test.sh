#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-kiroproxy:local}"
PORT="${PORT:-18080}"
NAME="${NAME:-kiroproxy-smoke}"

cleanup() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
}
trap cleanup EXIT

cleanup

docker run -d --name "$NAME" -p "${PORT}:8080" "$IMAGE" >/dev/null

for _ in $(seq 1 30); do
  code="$(curl -fsS -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/api/status" || true)"
  if [ "$code" = "200" ]; then
    echo "Smoke test passed: /api/status returned 200"
    exit 0
  fi
  sleep 1
done

echo "Smoke test failed: /api/status did not return 200" >&2
docker logs "$NAME" >&2 || true
exit 1
