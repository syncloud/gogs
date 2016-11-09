APP_NAME = 'gogs'
USER_NAME = 'git'
SYSTEMD_GOGS = 'gogs'
SYSTEMD_POSTGRESQL = 'gogs-postgresql'
PSQL_PATH = 'postgresql/bin/psql'
PSQL_DATA_PATH = 'database'
PSQL_PORT = 5433
DB_USER = 'git'
DB_PASS = 'git'
DB_NAME = 'gogs'
GOG_REPOS_DIR = 'gogs-repositories'
GOGS_PORT = 3000
GOGS_ADMIN_USER = 'gogs'
GOGS_ADMIN_PASSWORD = 'gogs'

from os.path import isdir, join
import requests
import time
from subprocess import check_output
import shutil
from syncloud_app import logger

from syncloud_platform.application import api
from syncloud_platform.gaplib import fs, linux, gen


def wait_url(url, timeout, interval = 1):
    t0 = time.clock()
    while time.clock() - t0 < timeout:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        time.sleep(interval)
    return False

def installed(database_path):
    return isdir(database_path)


def database_init(app_install_dir, database_path, user_name):
    log = logger.get_logger('postgres')
    if not isdir(database_path):
        psql_initdb = join(app_install_dir, 'postgresql/bin/initdb')
        log.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_install_dir, 'config', 'postgresql.conf')
        shutil.copy(postgresql_conf_from, postgresql_conf_to)
    else:
        log.info('Database path "{0}" already exists'.format(database_path))
    return database_path


class Database:

    def __init__(self, psql, database, user, database_path, port):
        self.psql = psql
        self.database = database
        self.user = user
        self.database_path = database_path
        self.port = port

    def execute(self, sql):
        log = logger.get_logger('postgres')
        log.info("executing: {0}".format(sql))
        command_line = '{0} -U {1} -d {2} -c "{3}" -h {4} -p {5}'.format(self.psql, self.user, self.database, sql, self.database_path, self.port)
        log.info(check_output(command_line, shell=True))


log = logger.get_logger('nextcloud_installer')

app = api.get_app_setup(APP_NAME)
app_dir = app.get_install_dir()
app_data_dir = app.get_data_dir()

home_folder = join('/home', USER_NAME)
linux.useradd(USER_NAME, home_folder=home_folder)

gogs_executable = join(app_dir, 'gogs', 'gogs')
check_output('chmod +x {0}'.format(gogs_executable), shell=True)

log_path = join(app_data_dir, 'log')
fs.makepath(log_path)

database_path = join(app_data_dir, PSQL_DATA_PATH)
gogs_repos_path = join(app_data_dir, GOG_REPOS_DIR)

variables = {
    'app_dir': app_dir,
    'app_data_dir': app_data_dir,
    'db_psql_path': database_path,
    'db_psql_port': PSQL_PORT,
    'db_name': DB_NAME,
    'db_user': DB_USER,
    'db_password': DB_PASS,
    'gogs_repos_path': gogs_repos_path,
    'log_path': log_path
}

templates_path = join(app_dir, 'config.templates')
config_path = join(app_dir, 'config')

gen.generate_files(templates_path, config_path, variables)

fs.chownpath(app_dir, USER_NAME, recursive=True)
fs.chownpath(app_data_dir, USER_NAME, recursive=True)

first_install = not installed(database_path)
if first_install:
    database_init(app_dir, database_path, DB_USER)

app.add_service(SYSTEMD_POSTGRESQL)

if first_install:
    db_postgres = Database(join(app_dir, PSQL_PATH), database='postgres', user=DB_USER, database_path=database_path, port=PSQL_PORT)
    db_postgres.execute("ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASS))
    db_postgres.execute("CREATE DATABASE {0} WITH OWNER={1};".format(DB_NAME, DB_USER))

app.add_service(SYSTEMD_GOGS)
app.register_web(GOGS_PORT)

app_url = app.app_url()


install_url = 'http://localhost:{}/install'.format(GOGS_PORT)

if not wait_url(install_url, timeout=5):
    log.error('Timeout waiting for url: {}', install_url)
    log.error('Failed to finish GOGS installation')
else:
    log.info("Making POST request to finish GOGS installation, url: {}".format(install_url))
    install_response = requests.post(install_url, data = {
        'db_type': 'PostgreSQL',
        'db_host': '{}:{}'.format(database_path, PSQL_PORT),
        'db_user': DB_USER,
        'db_passwd': DB_PASS,
        'db_name': DB_NAME,
        'ssl_mode': 'disable',
        'db_path': 'data/gogs.db',
        'app_name': 'Gogs: Go Git Service',
        'repo_root_path': gogs_repos_path,
        'run_user': USER_NAME,
        'domain': app_url,
        'ssh_port': '22',
        'http_port': str(GOGS_PORT),
        'app_url': '{}/'.format(app_url),
        'log_root_path': log_path,
        'smtp_host': '',
        'smtp_from': '',
        'smtp_email': '',
        'smtp_passwd': '',
        'disable_registration': 'on',
        'require_sign_in_view': 'on',
        'admin_name': GOGS_ADMIN_USER,
        'admin_passwd': GOGS_ADMIN_PASSWORD,
        'admin_confirm_passwd': GOGS_ADMIN_PASSWORD,
        'admin_email': app.redirect_email()
    })

    if install_response.status_code != 200:
        log.error('GOGS finish installation failed with status code: {}', install_response.status_code)
        log.error('GOGS finish installation POST request response:\n{}', str(install_response))
    else:
        log.info('GOGS finish installation succeded')