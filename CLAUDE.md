# CI

http://ci.syncloud.org:8080/syncloud/gogs

CI is Drone CI (JS SPA). Check builds via API:
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/gogs/builds?limit=5"
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
  --include "package python" \
  --include package \
  --include "test bookworm" \
  .drone.yml
```

Notes:
- `--trusted` is required for privileged/volume steps
- `--include` selects only listed steps (in pipeline order); omit to run all steps
- `drone jsonnet --stdout --stream` sends stderr to stderr (proto warnings are harmless)
