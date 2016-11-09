APP_NAME = 'gogs'
USER_NAME = 'git'
SYSTEMD_GOGS = 'gogs'
SYSTEMD_POSTGRESQL = 'gogs-postgresql'

from syncloud_platform.application import api
from syncloud_platform.gaplib import fs

app = api.get_app_setup(APP_NAME)

app.unregister_web()

app.remove_service(SYSTEMD_GOGS)
app.remove_service(SYSTEMD_POSTGRESQL)

app_dir = app.get_install_dir()

fs.removepath(app_dir)
