#!/bin/sh
# Nightly pg_dump with retention, run inside the db-backup container.
# Dumps land in ./backups on the host (custom format, restorable with
# pg_restore). Keeps BACKUP_KEEP_DAYS days.
set -eu

KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
BACKUP_HOUR="${BACKUP_HOUR_UTC:-1}"

backup() {
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  file="/backups/taskflow-${stamp}.dump"
  echo "[backup] writing ${file}"
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "${file}.part"
  mv "${file}.part" "${file}"
  find /backups -name 'taskflow-*.dump' -mtime +"${KEEP_DAYS}" -delete
  echo "[backup] done"
}

# Sleep until the next BACKUP_HOUR:00 UTC, back up, repeat. Plain
# arithmetic on epoch seconds - no date parsing, works in busybox.
while true; do
  now=$(date -u +%s)
  wait=$(( (BACKUP_HOUR * 3600 - now % 86400 + 86400) % 86400 ))
  [ "$wait" -eq 0 ] && wait=86400
  echo "[backup] next run in ${wait}s"
  sleep "$wait"
  backup || echo "[backup] FAILED" >&2
done
