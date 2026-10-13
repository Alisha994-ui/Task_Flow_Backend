# TaskFlow Backend – Production Deployment

The backend ships as one Docker image (`taskflow-backend`) and runs as a Compose stack behind the host's TLS proxy (Plesk). GitHub Actions tests every push, builds the image to GitHub Container Registry (GHCR) and deploys `main` to the server over SSH.

## 1. Architecture

```
Mobile app ──HTTPS──> Plesk nginx (TLS, Let's Encrypt)
                         │  http://127.0.0.1:8080
                         ▼
                   ┌─ nginx ────────── /static, /media (volumes)
   docker network  │    │ /api, /admin, /healthz
       "edge"      │    ▼
                   └─ web (gunicorn + Django) ──> Gemini, Firebase, SMTP
                          │
   docker network     ┌───┴──────────────┬─────────────┐
   "data" (internal)  db (Postgres 17)   scheduler     db-backup ──> ./backups
                      ▲                  (supercronic)
                      └── migrate (one-off: check, migrate, collectstatic)
```

| Service | Image | Role |
| --- | --- | --- |
| `db` | `postgres:17-alpine` | Database; volume `pgdata`; not published |
| `migrate` | app image | Runs `deploy/scripts/release.sh` once per deploy; `web` waits for it |
| `web` | app image | gunicorn on :8000; read-only filesystem; `/healthz/` checks the DB |
| `scheduler` | app image | `send_deadline_reminders` 03:00 UTC, `fix_project_progress` 02:30 UTC |
| `nginx` | `nginx:1.27-alpine` | Static/media files, proxy to `web`; bound to `127.0.0.1:8080` only |
| `db-backup` | `postgres:17-alpine` | Nightly `pg_dump` to `./backups`, 14-day retention |

Why a Postgres container instead of the server's Postgres 13: Django 6.1 does not support PostgreSQL 13, so the stack runs Postgres 17 itself.

## 2. One-time server setup (AlmaLinux + Plesk)

Install Docker Engine and the Compose plugin (skip if the Plesk Docker extension already installed Docker):

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
sudo dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

Create a deploy user and the application directory:

```bash
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo mkdir -p /opt/taskflow/secrets /opt/taskflow/backups
sudo chown -R deploy:deploy /opt/taskflow
```

Add the CI public key to `/home/deploy/.ssh/authorized_keys`.

As `deploy`, place the configuration:

```bash
cd /opt/taskflow
# from the repository: docker-compose.prod.yml, deploy/, .env.production.example
cp .env.production.example .env && chmod 600 .env
nano .env        # SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS, GEMINI_API_KEY, e-mail
# Firebase service account, readable by the container user (UID 10001)
cp firebase-admin.json secrets/firebase-admin.json
sudo chown 10001:10001 secrets/firebase-admin.json && sudo chmod 400 secrets/firebase-admin.json
```

### Plesk domain and TLS

1. Plesk > Websites & Domains > add `taskflow-api.kotenterprises.dev` and issue a Let's Encrypt certificate.
2. Hosting Settings: enable permanent SEO-safe 301 redirect from HTTP to HTTPS.
3. Apache & nginx Settings: untick **Proxy mode**, then in **Additional nginx directives** add:

```nginx
location ~ ^/ {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 90s;
    client_max_body_size 25m;
}
```

## 3. First deploy

```bash
cd /opt/taskflow
echo "<PAT with read:packages>" | docker login ghcr.io -u <github-user> --password-stdin   # private image only
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:8080/healthz/     # {"status": "ok"}
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Moving existing data from a development database:

```bash
# on the development machine
pg_dump -Fc -h localhost -U <dev_user> -d <dev_db> -f taskflow.dump
# on the server, after copying the file to /opt/taskflow
docker compose -f docker-compose.prod.yml exec -T db \
  pg_restore -U taskflow -d taskflow --no-owner --clean --if-exists < taskflow.dump
# uploaded files
docker run --rm -v taskflow_media:/dst -v "$PWD/media":/src alpine sh -c "cp -a /src/. /dst/ && chown -R 10001:10001 /dst"
```

## 4. CI/CD setup (GitHub)

Workflow: `.github/workflows/backend.yml`. Pull requests run tests only; `main` builds, pushes and deploys; `v*` tags also produce a versioned image.

| Name | Kind | Value |
| --- | --- | --- |
| `DEPLOY_HOST` | Secret | Server hostname or IP |
| `DEPLOY_USER` | Secret | `deploy` |
| `DEPLOY_SSH_KEY` | Secret | Private ed25519 key for `deploy` |
| `DEPLOY_KNOWN_HOSTS` | Secret | Output of `ssh-keyscan -t ed25519 <host>` |
| `GHCR_READ_TOKEN` | Secret | PAT with `read:packages` (private image only) |
| `DEPLOY_PORT` | Variable | SSH port, default 22 |
| `DEPLOY_PATH` | Variable | Default `/opt/taskflow` |

Create a GitHub environment named `production` and put the deploy secrets there; add required reviewers if deploys should need approval.

Each deploy records the image tag in `.env` (`IMAGE_TAG=sha-xxxxxxx`), keeps a timestamped `.env.bak.*`, starts the stack and fails the job if `/healthz/` is not healthy within 150 s.

## 5. Operations

| Task | Command (in `/opt/taskflow`, prefix `docker compose -f docker-compose.prod.yml`) |
| --- | --- |
| Status | `ps` |
| Logs | `logs -f --tail=200 web` (also `scheduler`, `migrate`, `nginx`) |
| Django shell | `exec web python manage.py shell` |
| Run a reminder now | `exec web python manage.py send_deadline_reminders --dry-run` |
| Restart the app | `restart web scheduler` |
| Manual backup | `exec -T db pg_dump -U taskflow -Fc taskflow > backups/manual-$(date +%F).dump` |
| Restore a backup | `exec -T db pg_restore -U taskflow -d taskflow --clean --if-exists < backups/taskflow-YYYYMMDD-HHMMSS.dump` |

**Rollback.** Set `IMAGE_TAG` in `.env` to the previous `sha-…` tag (see `.env.bak.*` or the GHCR package page), then `pull web && up -d`. If the bad release ran a migration that changed or dropped data, restore the backup taken before it; code rollback alone does not undo migrations.

**Rollback triggers.** `/healthz/` failing after deploy; login or task creation failing in the app; error rate in `logs web` rising after release.

## 6. Security notes

- `.env` and `secrets/` were present in the uploaded project archive. They are git-ignored, but treat the current `SECRET_KEY`, database password, Gemini key and Firebase key as exposed if that archive was shared anywhere, and rotate them for production.
- Files under `/media/` (task attachments, discussion files, profile photos) are served without authentication to anyone who has the URL. For confidential attachments, serve them through an authenticated Django view using nginx `X-Accel-Redirect`.
- Only nginx publishes a port, and only on `127.0.0.1`; Postgres sits on an internal network with no outbound route.
- Raise `SECURE_HSTS_SECONDS` to `31536000` once HTTPS has been stable for a few days.
