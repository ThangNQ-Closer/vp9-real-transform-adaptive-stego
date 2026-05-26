#!/bin/bash
set -euo pipefail
LAB="vp9-real-transform-adaptive-stego"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_IMAGE="labtainers/labtainer.base2"
BASE_ID="$(docker images -f=reference="${BASE_IMAGE}:latest" -q | head -1)"
if [ -z "$BASE_ID" ]; then
  docker pull "$BASE_IMAGE"
  BASE_ID="$(docker images -f=reference="${BASE_IMAGE}:latest" -q | head -1)"
fi
if [ -z "$BASE_ID" ]; then
  echo "Could not determine Docker image id for $BASE_IMAGE" >&2
  exit 1
fi
BASE_LABEL="${BASE_IMAGE}.${BASE_ID}"
make_role_tar() {
  local role="$1"
  local work
  work="$(mktemp -d)"
  rsync -a --exclude='home_tar/' --exclude='sys_tar/' --exclude='*.tar.gz' "$ROOT/$role/" "$work/"
  mkdir -p "$work/.local/config" "$work/.local/bin" "$work/.local/result"
  cp "$ROOT/config/"* "$work/.local/config/" 2>/dev/null || true
  if [ -f "$ROOT/$role/prestop" ]; then cp "$ROOT/$role/prestop" "$work/.local/bin/prestop"; chmod +x "$work/.local/bin/prestop"; fi
  tar -czf "$ROOT/$role/${LAB}.${role}.student.tar.gz" -C "$work" .
  rm -rf "$work"
  mkdir -p "$ROOT/$role/sys_tar"
  tar -cf "$ROOT/$role/sys_tar/sys.tar" --files-from /dev/null
  tar -czf "$ROOT/$role/sys_${LAB}.${role}.student.tar.gz" --files-from /dev/null
  mkdir -p "$ROOT/$role/home_tar"
  list_file="$ROOT/config/${role}-home_tar.list"
  if [ -f "$list_file" ]; then
    include_file="$(mktemp)"
    while IFS= read -r item; do
      [ -z "$item" ] && continue
      [ -e "$ROOT/$role/$item" ] && echo "$item" >> "$include_file"
    done < "$list_file"
    if [ -s "$include_file" ]; then
      tar -cf "$ROOT/$role/home_tar/home.tar" -C "$ROOT/$role" -T "$include_file"
    else
      tar -cf "$ROOT/$role/home_tar/home.tar" --files-from /dev/null
    fi
    rm -f "$include_file"
  else
    tar -cf "$ROOT/$role/home_tar/home.tar" --files-from /dev/null
  fi
}
make_role_tar sender
make_role_tar receiver
(
  cd "$ROOT/sender"
  docker build --build-arg registry=labtainers --build-arg lab=${LAB}.sender.student --build-arg labdir=. --build-arg imagedir=. --build-arg user_name=student --build-arg password=student --build-arg apt_source=archive.ubuntu.com --build-arg version=3 --build-arg base="$BASE_LABEL" -t ${LAB}.sender.student:latest -f "$ROOT/dockerfiles/Dockerfile.${LAB}.sender.student" .
)
(
  cd "$ROOT/receiver"
  docker build --build-arg registry=labtainers --build-arg lab=${LAB}.receiver.student --build-arg labdir=. --build-arg imagedir=. --build-arg user_name=student --build-arg password=student --build-arg apt_source=archive.ubuntu.com --build-arg version=3 --build-arg base="$BASE_LABEL" -t ${LAB}.receiver.student:latest -f "$ROOT/dockerfiles/Dockerfile.${LAB}.receiver.student" .
)
echo "Built local Labtainer images."
