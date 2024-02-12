#!/bin/bash
image_name=discord-archive-bot
archive_path=./archive  # host archive path

docker image prune --force # -a
docker build . -t $image_name # --force-rm --no-cache
docker run -it --rm --env-file=.env -v $archive_path:/archive $image_name