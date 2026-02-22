# CI

http://ci.syncloud.org:8080/syncloud/gogs

CI is Drone CI (JS SPA). Check builds via API:
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/gogs/builds?limit=5"
```

## CI Artifacts

Artifacts are served at `http://ci.syncloud.org:8081` (returns JSON directory listings).

Browse the top level for a build (returns distro subdirs + snap file):
```
curl -s "http://ci.syncloud.org:8081/files/gogs/{build}-{arch}/"
```

Each distro dir contains `app/`, `platform/`, and for upgrade/UI tests also `desktop/`, `refresh.journalctl.log`, `video.mkv`:
```
curl -s "http://ci.syncloud.org:8081/files/gogs/{build}-{arch}/{distro}/"
curl -s "http://ci.syncloud.org:8081/files/gogs/{build}-{arch}/{distro}/app/"
curl -s "http://ci.syncloud.org:8081/files/gogs/{build}-{arch}/{distro}/desktop/"
```

Directory structure:
```
{build}-{arch}/
  {distro}/
    app/
      journalctl.log          # full journal from integration test teardown
      gogs.log, gorm.log      # app logs
      ps.log, netstat.log     # process/network state at teardown
    platform/                 # platform logs
    desktop/                  # UI test artifacts (amd64 only)
      journalctl.log
      screenshot/
        {test-name}.png
        {test-name}.html.log
      log/
        gogs.log
    refresh.journalctl.log    # full journal from upgrade test (pre/post-refresh)
    database.dump             # pg_dumpall captured during upgrade test teardown
    video.mkv                 # selenium recording
```

Download a file directly:
```
curl -O "http://ci.syncloud.org:8081/files/gogs/282-amd64/buster/refresh.journalctl.log"
curl -O "http://ci.syncloud.org:8081/files/gogs/282-amd64/buster/app/journalctl.log"
curl -O "http://ci.syncloud.org:8081/files/gogs/282-amd64/bookworm/desktop/journalctl.log"
```

# Running Drone builds locally

Generate `.drone.yml` from jsonnet (run from project root):
```
drone jsonnet --stdout --stream > .drone.yml
```

Run a specific pipeline with selected steps (e.g. amd64 up to `test bookworm`):
```
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
  --include "test bookworm" \
  .drone.yml
```

Notes:
- `--trusted` is required for privileged/volume steps
- `--include` selects only listed steps (in pipeline order); omit to run all steps
- `drone jsonnet --stdout --stream` sends stderr to stderr (proto warnings are harmless)
- `test bookworm` requires the `gogs.bookworm.com` platform service container to be reachable; `drone exec` does not start services, so run `test-local.sh` instead for a full end-to-end run

# Running locally (full end-to-end)

`test-local.sh` runs the complete pipeline locally without pushing to CI:
```
./test-local.sh
```

It:
1. Cleans previous build output (via Docker, since build steps run as root)
2. Regenerates `.drone.yml` from jsonnet
3. Creates a Docker network (`gogs-local`) and starts the `gogs.bookworm.com` platform service container
4. Runs all build steps via `drone exec` (version → package)
5. Runs `test bookworm` in a Python container connected to the platform network
6. Streams all output to `test-local.log` and stdout
7. Cleans up the platform container and network on exit
