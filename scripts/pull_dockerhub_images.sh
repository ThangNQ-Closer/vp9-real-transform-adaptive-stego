#!/bin/bash
set -euo pipefail
DOCKERHUB_REPO="${DOCKERHUB_REPO:-closer031004/vp9-real-transform-adaptive-stego}"
docker pull "$DOCKERHUB_REPO:sender-student"
docker pull "$DOCKERHUB_REPO:receiver-student"
docker tag "$DOCKERHUB_REPO:sender-student" vp9-real-transform-adaptive-stego.sender.student:latest
docker tag "$DOCKERHUB_REPO:receiver-student" vp9-real-transform-adaptive-stego.receiver.student:latest
echo "Tagged Labtainer images:"
docker images | grep 'vp9-real-transform-adaptive-stego' || true
