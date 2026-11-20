#!/usr/bin/env bash
# Manual database backup and restore test (SOP-11 C and D).
# Usage:  DATABASE_URL="<External Database URL from Render>" ./scripts/backup_db.sh
# Makes allura_db_YYYY-MM-DD.dump, checks it can be read, and (if a local PostgreSQL is running)
# restores it into a throw-away database allura_db_restore_test and counts the main tables.
set -euo pipefail
: "${DATABASE_URL:?Set DATABASE_URL to the External Database URL from Render}"
name="allura_db_$(date +%Y-%m-%d).dump"
pg_dump "$DATABASE_URL" -Fc -f "$name"
pg_restore --list "$name" > /dev/null
echo "Backup written: $name ($(du -h "$name" | cut -f1))"

if command -v createdb > /dev/null && pg_isready -q 2>/dev/null; then
  dropdb --if-exists allura_db_restore_test
  createdb allura_db_restore_test
  pg_restore --no-owner -d allura_db_restore_test "$name" || true
  echo "Restore test (rows per table):"
  for t in items accounts inquiries site_content; do
    printf "  %-14s %s\n" "$t" "$(psql -tA -d allura_db_restore_test -c "SELECT COUNT(*) FROM $t" 2>/dev/null || echo 'missing')"
  done
  echo "Compare these counts with the admin site (Items, Accounts, Inquiries). Upload $name to 06 Codes › Database Backups."
fi
