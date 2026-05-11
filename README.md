# KiroProxy Docker Image

This repository builds a container image for [petehsu/KiroProxy](https://github.com/petehsu/KiroProxy), following the same image-recipe pattern as [yangchuansheng/frappe-hrms-v16-docker](https://github.com/yangchuansheng/frappe-hrms-v16-docker): this repo stores the Docker build recipe, resolves the upstream revision in GitHub Actions, and publishes the final image to GitHub Container Registry.

Published image:

```text
ghcr.io/yangchuansheng/kiroproxy:latest
```

## What is included

- `Containerfile` builds KiroProxy from a selectable upstream branch, tag, or commit SHA.
- `.github/workflows/build.yml` builds and pushes to GHCR on push, schedule, or manual dispatch.
- `docker-compose.yml` provides a simple persistent runtime using `/data` as the container home.
- `entrypoint.sh` starts the service in headless mode and keeps KiroProxy config under `/data`.

## Image patches

The image build applies a small runtime patch to upstream KiroProxy before installing dependencies:

- Adds `claude-opus-4.6` and `claude-opus-4.7` to `KIRO_MODELS`.
- Preserves exact passthrough for those model IDs.
- Maps `opus`, `opus-4.7`, and `claude-4-opus` to `claude-opus-4.7`.
- Maps `opus-4.6` to `claude-opus-4.6`.
- Adds both IDs to the `/v1/models` static fallback list.

The workflow validates this patch before building the image.

## Manual build

```bash
docker build   --build-arg KIROPROXY_REF=main   --tag ghcr.io/yangchuansheng/kiroproxy:latest   --file Containerfile .
```

To pin a build to a specific upstream commit:

```bash
docker build   --build-arg KIROPROXY_REF=d34a0a78530823231fd6ec81245c8a83d0065bac   --tag ghcr.io/yangchuansheng/kiroproxy:d34a0a785308   --file Containerfile .
```

## Run with Docker Compose

```bash
cp .env.example .env
docker compose up -d
```

Open:

```text
http://localhost:8080
```

KiroProxy stores account configuration in the `/data` volume. You can add accounts through the Web UI, import an exported account file, or mount an existing AWS SSO cache into `/data/.aws/sso/cache` as shown in `docker-compose.yml`.

## Run with Docker

```bash
docker run -d   --name kiroproxy   -p 8080:8080   -v kiroproxy-data:/data   ghcr.io/yangchuansheng/kiroproxy:latest
```

## Trigger a build

Use GitHub Actions → **Build KiroProxy image** → **Run workflow**.

Inputs:

- `image_tag`: image tag to publish, default `latest`.
- `kiroproxy_ref`: KiroProxy branch, tag, or commit SHA, default `main`.
- `platforms`: Docker platforms, default `linux/amd64`.

## Runtime notes

- The container listens on port `8080` by default.
- `HOME` is set to `/data`, so KiroProxy reads and writes `/data/.kiro-proxy` and `/data/.aws/sso/cache`.
- The entrypoint starts as root only long enough to create and fix ownership of `/data`, then drops privileges to the `kiroproxy` user before launching the app.
- If imported credentials lack `profileArn`, set `KIRO_PROFILE_ARN` in `docker-compose.yml` or the container environment.

## Smoke test

After building locally:

```bash
IMAGE=ghcr.io/yangchuansheng/kiroproxy:latest ./scripts/smoke-test.sh
```

The smoke test checks `GET /api/status` and expects HTTP `200`.
