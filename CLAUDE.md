# CI

http://ci.syncloud.org:8080/syncloud/gogs

CI is Drone CI (JS SPA). Check builds via API:
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/gogs/builds?limit=5"
```

## CI Artifacts

Artifacts are served at `http://ci.syncloud.org:8081` (nginx file browser SPA).
Browse via API with `curl -s "http://ci.syncloud.org:8081/files/{repo}/{build}-{arch}/{suite}/desktop/"`.

Example for build 272, amd64, bookworm:
```
curl -s "http://ci.syncloud.org:8081/files/gogs/272-amd64/bookworm/desktop/"
```

Directory structure:
```
desktop/
  journalctl.log              # systemd journal from the UI test run
  screenshot/
    {test-name}.png           # screenshot taken during the test
    {test-name}.html.log      # page source at the time of the screenshot
  log/
    gogs.log
    gorm.log
    xorm.log
```

Download a file directly:
```
curl -O "http://ci.syncloud.org:8081/files/gogs/272-amd64/bookworm/desktop/screenshot/no-registration-desktop.png"
curl -O "http://ci.syncloud.org:8081/files/gogs/272-amd64/bookworm/desktop/journalctl.log"
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
