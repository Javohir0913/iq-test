#!/usr/bin/env bash
# Serverda yangilash: kodni GitHub'dan olib, konteynerlarni qayta quradi.
#   cd ~/iq-test && ./deploy/update.sh
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only
docker compose -f docker-compose.yml up -d --build --remove-orphans
docker image prune -f >/dev/null
docker compose -f docker-compose.yml ps
