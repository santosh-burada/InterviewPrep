#!/bin/bash

# Image to delete
IMAGE_NAME="santoshburada/backend:v1.0"

# Iterate over all Kind node containers
for NODE in $(docker ps --filter "name=multi-cluster" --format "{{.Names}}"); do
  echo "Deleting image from $NODE..."
  docker exec -it $NODE crictl rmi $IMAGE_NAME
done

echo "Image deletion complete."
