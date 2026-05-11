ARG PYTHON_VERSION=3.12
ARG KIROPROXY_REPO=https://github.com/petehsu/KiroProxy.git
ARG KIROPROXY_REF=main

FROM python:${PYTHON_VERSION}-slim AS source
ARG KIROPROXY_REPO
ARG KIROPROXY_REF
WORKDIR /src
COPY scripts/patch_kiroproxy_models.py /tmp/patch_kiroproxy_models.py
RUN apt-get update   && apt-get install -y --no-install-recommends ca-certificates git   && rm -rf /var/lib/apt/lists/*   && git init   && git remote add origin "${KIROPROXY_REPO}"   && git fetch --depth 1 origin "${KIROPROXY_REF}"   && git checkout --detach FETCH_HEAD   && rm -rf .git   && python /tmp/patch_kiroproxy_models.py /src

FROM python:${PYTHON_VERSION}-slim AS builder
ENV VIRTUAL_ENV=/opt/venv     PATH=/opt/venv/bin:$PATH     PIP_DISABLE_PIP_VERSION_CHECK=1     PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m venv "$VIRTUAL_ENV"
COPY --from=source /src/requirements.txt ./requirements.txt
RUN pip install --upgrade pip setuptools wheel   && pip install -r requirements.txt

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG KIROPROXY_REPO
ARG KIROPROXY_REF
LABEL org.opencontainers.image.title="KiroProxy"       org.opencontainers.image.description="Container image for petehsu/KiroProxy"       org.opencontainers.image.source="https://github.com/petehsu/KiroProxy"       org.opencontainers.image.url="https://github.com/petehsu/KiroProxy"
ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     VIRTUAL_ENV=/opt/venv     PATH=/opt/venv/bin:$PATH     HOME=/data     PORT=8080
RUN apt-get update   && apt-get install -y --no-install-recommends ca-certificates tini gosu   && rm -rf /var/lib/apt/lists/*   && groupadd --system --gid 10001 kiroproxy   && useradd --system --uid 10001 --gid kiroproxy --home-dir /data --shell /usr/sbin/nologin kiroproxy   && mkdir -p /app /data/.kiro-proxy /data/.aws/sso/cache   && chown -R kiroproxy:kiroproxy /app /data
COPY --from=builder --chown=kiroproxy:kiroproxy /opt/venv /opt/venv
COPY --from=source --chown=kiroproxy:kiroproxy /src /app
COPY --chown=root:root entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
USER root
WORKDIR /app
VOLUME ["/data"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3   CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8080') + '/api/status', timeout=3).read()" || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["serve"]
