#!/usr/bin/env sh
set -eu
docker compose config
docker compose up --build -d
docker compose ps
curl --fail http://localhost:8000/api/v1/health
docker compose exec -T api pytest -q
