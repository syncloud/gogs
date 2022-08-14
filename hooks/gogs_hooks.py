import logging
import shutil
import time
import uuid
from os import path, environ
from os.path import isdir, join
from subprocess import check_output

import requests_unixsocket
from bs4 import BeautifulSoup
from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage, users

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
GOGS_ADMIN_USER = 'gogs'
GOGS_ADMIN_PASSWORD = uuid.uuid4().hex

logger.init(logging.DEBUG, console=True, line_format='%(message)s')

install_file = join(paths.get_data_dir(APP_NAME), 'installed')


def wait_url(log, url, timeout, interval=3):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            session = requests_unixsocket.Session()
            log.info('waiting for url: {0}'.format(url))
            response = session.get(url, allow_redirects=False)
            if response.status_code == 200 or response.status_code == 302:
                return
            log.info(response.status_code)
        except Exception as e:
            log.info(e.message)
        time.sleep(interval)
    raise Exception('Timeout waiting for url: {0}'.format(url))


def database_init(app_dir, app_data_dir, database_path, user_name):
    log = logger.get_logger('gogs')
    if not isdir(database_path):
        psql_initdb = join(app_dir, 'postgresql/bin/initdb')
        log.info(check_output(['sudo', '-H', '-u', user_name, psql_initdb, database_path]))
        postgresql_conf_to = join(database_path, 'postgresql.conf')
        postgresql_conf_from = join(app_data_dir, 'config', 'postgresql.conf')
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
        command_line = '{0} -U {1} -d {2} -c "{3}" -h {4} -p {5}'.format(self.psql, self.user, self.database, sql,
                                                                         self.database_path, self.port)
        log.info(check_output(command_line, shell=True))


def install():
    app_dir = paths.get_app_dir(APP_NAME)
    app_data_dir = paths.get_data_dir(APP_NAME)

    home_folder = join('/home', USER_NAME)
    linux.useradd(USER_NAME, home_folder=home_folder)

    log_path = join(app_data_dir, 'log')
    fs.makepath(log_path)

    database_path = join(app_data_dir, PSQL_DATA_PATH)
    gogs_repos_path = storage.init_storage(APP_NAME, USER_NAME)
    app_url = urls.get_app_url(APP_NAME)

    variables = {
        'app_dir': app_dir,
        'app_data_dir': app_data_dir,
        'db_psql_path': database_path,
        'db_psql_port': PSQL_PORT,
        'db_name': DB_NAME,
        'db_user': DB_USER,
        'db_password': DB_PASS,
        'gogs_repos_path': gogs_repos_path,
        'log_path': log_path,
        'app_url': app_url,
        'web_secret': uuid.uuid4().hex,
        'disable_registration': False
    }

    templates_path = join(app_dir, 'config')
    config_path = join(app_data_dir, 'config')

    gen.generate_files(templates_path, config_path, variables)
    if 'SNAP' not in environ:
        fs.chownpath(app_dir, USER_NAME, recursive=True)
    fs.chownpath(app_data_dir, USER_NAME, recursive=True)

    if not path.isfile(install_file):
        database_init(app_dir, app_data_dir, database_path, DB_USER)


def database_post_start():
    log = logger.get_logger('gogs')

    if path.isfile(install_file):
        log.info('database is already configured')
        return

    app_dir = paths.get_app_dir(APP_NAME)
    app_data_dir = paths.get_data_dir(APP_NAME)
    database_path = join(app_data_dir, PSQL_DATA_PATH)

    log.info('creating database')
    db_postgres = Database(join(app_dir, PSQL_PATH),
                           database='postgres', user=DB_USER, database_path=database_path, port=PSQL_PORT)
    db_postgres.execute("ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASS))
    db_postgres.execute("CREATE DATABASE {0} WITH OWNER={1};".format(DB_NAME, DB_USER))


def configure():
    log = logger.get_logger('gogs')

    if path.isfile(install_file):
        log.info('gogs is already configured')
        return

    app_dir = paths.get_app_dir(APP_NAME)
    app_data_dir = paths.get_data_dir(APP_NAME)
    database_path = join(app_data_dir, PSQL_DATA_PATH)

    socket = '{0}/web.socket'.format(app_data_dir).replace('/', '%2F')
    index_url = 'http+unix://{0}'.format(socket)

    create_install_user(index_url, log, users.get_email(), GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
    activate_ldap(index_url, log, GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
    delete_install_user(index_url, log, GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)

    db = Database(join(app_dir, PSQL_PATH),
                  database=DB_NAME, user=DB_USER, database_path=database_path, port=PSQL_PORT)
    db.execute("select * from login_source;")

    with open(install_file, 'w') as f:
        f.write('installed\n')


def create_install_user(index_url, log, email, login, password):
    signup_url = '{0}/user/sign_up'.format(index_url)

    wait_url(log, index_url, timeout=60)

    log.info("Creating an install user, email: {0} url: {1}".format(email, signup_url))
    session = requests_unixsocket.Session()
    response = session.post(signup_url, allow_redirects=False, timeout=120, data={
        'user_name': login,
        'password': password,
        'retype': password,
        'email': email
    })

    if response.status_code != 302:
        log.error('failed with status code: {0}'.format(response.status_code))
        log.error(response.text.encode("utf-8"))
        raise Exception('unable to create install user')
    else:
        log.info('install user created')


def delete_install_user(socket, log, username, password):
    log.info('getting csrf to delete install user')
    session = gogs_login(socket, log, username, password)
    user_url = '{0}/admin/users/1/delete'.format(socket)
    csrf = extract_csrf(session.get(user_url).text)

    log.info('deleting install user')
    response = session.post(user_url, allow_redirects=False,
                            data={'id': 1, '_csrf': csrf})

    if response.status_code != 200:
        log.error('status code: {0}'.format(response.status_code))
        log.error(response.text.encode("utf-8"))
        raise Exception('unable to delete install user')


def gogs_login(socket, log, username, password):
    wait_url(log, socket, timeout=60)

    session = requests_unixsocket.Session()

    login_url = '{0}/user/login'.format(socket)
    login_csrf = extract_csrf(session.get(login_url).text)
    response = session.post(login_url,
                            data={'user_name': username, 'password': password,
                                  '_csrf': login_csrf},
                            allow_redirects=False)

    if response.status_code != 302:
        log.error('status code: {0}'.format(response.status_code))
        log.error(response.text.encode("utf-8"))
        raise Exception('unable to login')

    return session


def activate_ldap(socket, log, username, password):
    log.info('activating ldap')
    session = gogs_login(socket, log, username, password)

    auth_url = '{0}/admin/auths/new'.format(socket)
    auth_csrf = extract_csrf(session.get(auth_url).text)

    auth_response = session.post(auth_url,
                                 data={
                                     '_csrf': auth_csrf,
                                     'type': 5,
                                     'name': 'syncloud',
                                     'security_protocol': '',
                                     'host': 'localhost',
                                     'port': 389,
                                     'bind_dn': '',
                                     'bind_password': '',
                                     'user_base': '',
                                     'user_dn': 'cn=%s,ou=users,dc=syncloud,dc=org',
                                     'filter': '(&(objectclass=inetOrgPerson)(uid=%s))',
                                     'admin_filter': '(objectClass=inetOrgPerson)',
                                     'attribute_username': 'cn',
                                     'attribute_name': 'cn',
                                     'attribute_surname': '',
                                     'attribute_mail': 'mail',
                                     'group_dn': '',
                                     'group_filter': '',
                                     'group_member_uid': '',
                                     'user_uid': '',
                                     'smtp_auth': 'PLAIN',
                                     'smtp_host': '',
                                     'smtp_port': '',
                                     'allowed_domains': '',
                                     'pam_service_name': '',
                                     'is_active': 'on'},
                                 allow_redirects=False)

    if auth_response.status_code != 302:
        log.error('status code: {0}'.format(auth_response.status_code))
        log.error(auth_response.text.encode("utf-8"))
        raise Exception('unable to enable ldap')


def extract_csrf(response):
    soup = BeautifulSoup(response, "html.parser")
    return soup.find_all('meta', {'name': '_csrf'})[0]['content']


def prepare_storage():
    storage.init_storage(APP_NAME, USER_NAME)
