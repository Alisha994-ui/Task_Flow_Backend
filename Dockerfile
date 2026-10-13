# syntax=docker/dockerfile:1.7
#
# TaskFlow backend - production image.
#
#   docker build -t taskflow-backend .
#
# Two stages: dependencies are compiled in "builder" and only the finished
# virtualenv is copied into "runtime", so no compiler ends up in production.

ARG PYTHON_VERSION=3.13

# ---------------------------------------------------------------- builder
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# ---------------------------------------------------------------- runtime
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Cron runner for the scheduler container; pinned and checksum-verified.
ARG SUPERCRONIC_VERSION=v0.2.33
ARG SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8

LABEL org.opencontainers.image.title="taskflow-backend" \
      org.opencontainers.image.description="TaskFlow Django REST API" \
      org.opencontainers.image.vendor="KOT Enterprises"

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    STATIC_ROOT=/app/staticfiles \
    MEDIA_ROOT=/app/media \
    FIREBASE_CREDENTIALS_FILE=/run/secrets/firebase-admin.json

# libpq5: runtime for psycopg2; curl: health checks; tini: proper PID 1
# (signal forwarding, zombie reaping) for gunicorn and supercronic.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl tini ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSLo /usr/local/bin/supercronic \
      "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
 && echo "${SUPERCRONIC_SHA1SUM}  /usr/local/bin/supercronic" | sha1sum -c - \
 && chmod +x /usr/local/bin/supercronic

# Unprivileged user; fixed UID so volume ownership is predictable.
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
# Code stays root-owned (read-only to the app user); only the two data
# directories are writable.
COPY . .
RUN chmod +x /app/deploy/scripts/*.sh \
 && mkdir -p /app/staticfiles /app/media \
 && chown -R app:app /app/staticfiles /app/media

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz/ || exit 1

ENTRYPOINT ["/usr/bin/tini", "--"]

# Workers: 2 x CPU + 1 is the usual start; tune with GUNICORN_WORKERS.
# Timeout is above the assistant's 45 s model budget.
CMD ["sh", "-c", "exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-3} \
  --threads ${GUNICORN_THREADS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-60} \
  --graceful-timeout 30 \
  --max-requests 1000 --max-requests-jitter 100 \
  --worker-tmp-dir /dev/shm \
  --forwarded-allow-ips='*' \
  --access-logfile - --error-logfile -"]
