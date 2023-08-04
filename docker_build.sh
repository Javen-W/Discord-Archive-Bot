#!/bin/bash
imageName=discord-archive-bot
# containerName=discord-archive-bot
docker image prune --force # -a
docker build . -t $imageName # --force-rm --no-cache
docker run --rm -e DISCORD_TOKEN="$DISCORD_TOKEN" $imageName # -t --name $containerName

