#!/bin/bash
set -eo pipefail

LOG=test-local.log
BOOKWORM_CONTAINER=gogs.bookworm.com
BUSTER_CONTAINER=gogs.buster.com
SELENIUM_CONTAINER=selenium
NETWORK=gogs-local

cleanup() {
  echo "--- cleanup ---"
  docker rm -f "$BOOKWORM_CONTAINER" "$BUSTER_CONTAINER" "$SELENIUM_CONTAINER" 2>/dev/null || true
  docker network rm "$NETWORK" 2>/dev/null || true
}
trap cleanup EXIT

# Clean previous build output and artifacts (Docker runs as root, so use docker to remove)
docker run --rm -v "$(pwd):/src" alpine sh -c "rm -rf /src/build/* /src/artifact /src/*.snap && mkdir -p /src/artifact"

# Generate .drone.yml properly (stderr goes to terminal, not into the file)
drone jsonnet --stdout --stream > .drone.yml

# Create network and start platform service containers (drone exec does not start services)
docker network create "$NETWORK"
docker run -d \
  --name "$BOOKWORM_CONTAINER" \
  --network "$NETWORK" \
  --privileged \
  -v /var/run/dbus:/var/run/dbus \
  -v /dev:/dev \
  syncloud/platform-bookworm-amd64:25.09

docker run -d \
  --name "$BUSTER_CONTAINER" \
  --network "$NETWORK" \
  --privileged \
  -v /var/run/dbus:/var/run/dbus \
  -v /dev:/dev \
  syncloud/platform-buster-amd64:25.02

docker run -d \
  --name "$SELENIUM_CONTAINER" \
  --network "$NETWORK" \
  --shm-size=2g \
  -e SE_NODE_SESSION_TIMEOUT=999999 \
  selenium/standalone-firefox:4.35.0-20250828

# Run all build steps (none require the platform service)
drone exec --pipeline amd64 --trusted \
  --include version \
  --include gogs \
  --include "gogs test" \
  --include nginx \
  --include "nginx test" \
  --include postgresql \
  --include "postgresql test" \
  --include "package git" \
  --include "git test" \
  --include cli \
  --include package \
  .drone.yml 2>&1 | tee "$LOG"

# Run test bookworm manually so it can reach the platform service container
docker run --rm \
  --network "$NETWORK" \
  -v "$(pwd):/drone/src" \
  -w /drone/src \
  python:3.12-slim-bookworm \
  bash -c "APP_ARCHIVE_PATH=\$(realpath \$(cat package.name)) && cd test && ./deps.sh && py.test -x -s test.py --distro=bookworm --app-archive-path=\$APP_ARCHIVE_PATH --app=gogs --device-user=gogs --arch=amd64" \
  2>&1 | tee -a "$LOG"

# Run test buster
docker run --rm \
  --network "$NETWORK" \
  -v "$(pwd):/drone/src" \
  -w /drone/src \
  python:3.12-slim-bookworm \
  bash -c "APP_ARCHIVE_PATH=\$(realpath \$(cat package.name)) && cd test && ./deps.sh && py.test -x -s test.py --distro=buster --app-archive-path=\$APP_ARCHIVE_PATH --app=gogs --device-user=gogs --arch=amd64" \
  2>&1 | tee -a "$LOG"

# Run upgrade test on buster
docker run --rm \
  --network "$NETWORK" \
  -v "$(pwd):/drone/src" \
  -w /drone/src \
  python:3.12-slim-bookworm \
  bash -c "APP_ARCHIVE_PATH=\$(realpath \$(cat package.name)) && cd test && ./deps.sh && py.test -x -s upgrade.py --distro=buster --app-archive-path=\$APP_ARCHIVE_PATH --app=gogs --device-user=gogs --browser=firefox" \
  2>&1 | tee -a "$LOG"
