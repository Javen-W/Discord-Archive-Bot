#!/bin/bash
set -euo pipefail

image_name=discord-archive-bot
archive_path=./archive  # host archive path
logs_path=./logs        # host logs path

# Ensure host directories exist before mounting
mkdir -p "$archive_path" "$logs_path"

docker image prune --force # -a
docker build . -t $image_name # --force-rm --no-cache
docker run -it --rm \
    --env-file=.env \
    -v "$(realpath $archive_path)":/archive \
    -v "$(realpath $logs_path)":/usr/app/logs \
    $image_name