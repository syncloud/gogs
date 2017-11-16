from os.path import dirname, join, abspath, isdir
from os import listdir
import sys

app_path = abspath(join(dirname(__file__), '..'))

lib_path = join(app_path, 'lib')
libs = [join(lib_path, item) for item in listdir(lib_path) if isdir(join(lib_path, item))]
map(sys.path.append, libs)
from bs4 import BeautifulSoup

from os.path import isdir, join
import requests_unixsocket
import time
from subprocess import check_output
import shutil
import uuid
from syncloud_app import logger

from syncloud_platform.application import api
from syncloud_platform.gaplib import fs, linux, gen

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
GOGS_ADMIN_PASSWORD = unicode(uuid.uuid4().hex)


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
        except Exception, e:
            log.info(e.message)
        time.sleep(interval)
    raise Exception('Timeout waiting for url: {0}'.format(url))


def installed(database_path):
    return isdir(database_path)


def database_init(app_dir, app_data_dir, database_path, user_name):
    log = logger.get_logger('postgres')
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
    log = logger.get_logger('gogs_installer')

    linux.fix_locale()

    app = api.get_app_setup(APP_NAME)
    app_dir = app.get_install_dir()
    app_data_dir = app.get_data_dir()

    home_folder = join('/home', USER_NAME)
    linux.useradd(USER_NAME, home_folder=home_folder)

    log_path = join(app_data_dir, 'log')
    fs.makepath(log_path)

    database_path = join(app_data_dir, PSQL_DATA_PATH)
    gogs_repos_path = app.get_storage_dir()

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
        'app_url': app.app_url(),
        'web_secret': unicode(uuid.uuid4().hex),
        'disable_registration': False
    }

    templates_path = join(app_dir, 'config.templates')
    config_path = join(app_data_dir, 'config')

    gen.generate_files(templates_path, config_path, variables)

    fs.chownpath(app_dir, USER_NAME, recursive=True)
    fs.chownpath(app_data_dir, USER_NAME, recursive=True)

    first_install = not installed(database_path)
    if first_install:
        database_init(app_dir, app_data_dir, database_path, DB_USER)
        prepare_storage()

    app.add_service(SYSTEMD_POSTGRESQL)

    if first_install:
        log.info('creating database')
        db_postgres = Database(join(app_dir, PSQL_PATH),
                               database='postgres', user=DB_USER, database_path=database_path, port=PSQL_PORT)
        db_postgres.execute("ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASS))
        db_postgres.execute("CREATE DATABASE {0} WITH OWNER={1};".format(DB_NAME, DB_USER))

    app.add_service(SYSTEMD_GOGS)

    socket = '{0}/web.socket'.format(app_data_dir).replace('/', '%2F')
    index_url = 'http+unix://{0}'.format(socket)
    if first_install:
        create_install_user(index_url, log, app.redirect_email(), GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
        activate_ldap(index_url, log, GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
        delete_install_user(index_url, log, GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)

    db = Database(join(app_dir, PSQL_PATH),
                  database=DB_NAME, user=DB_USER, database_path=database_path, port=PSQL_PORT)
    db.execute("select * from login_source;")


def create_install_user(index_url, log, email, login, password):

    signup_url = '{0}/user/sign_up'.format(index_url)

    wait_url(log, index_url, timeout=60)

    log.info("Creating an install user, url: {0}".format(signup_url))
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
    session = login(socket, log, username, password)
    user_url = '{0}/admin/users/1/delete'.format(socket)
    csrf = extract_csrf(session.get(user_url).text)

    log.info('deleting install user')
    response = session.post(user_url, allow_redirects=False,
                            data={'id': 1, '_csrf': csrf})

    if response.status_code != 200:
        log.error('status code: {0}'.format(response.status_code))
        log.error(response.text.encode("utf-8"))
        raise Exception('unable to delete install user')


def login(socket, log, username, password):
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
    session = login(socket, log, username, password)

    auth_url = '{0}/admin/auths/new'.format(socket)
    auth_csrf = extract_csrf(session.get(auth_url).text)

    auth_response = session.post(auth_url,
                                 data={
                                      '_csrf': auth_csrf,
                                      'type': 2,
                                      'name': 'syncloud',
                                      'security_protocol': '',
                                      'host': 'localhost',
                                      'port': 389,
                                      'bind_dn': 'dc=syncloud,dc=org',
                                      'bind_password': 'syncloud',
                                      'user_base': 'ou=users,dc=syncloud,dc=org',
                                      'user_dn': '',
                                      'filter': '(&(objectclass=inetOrgPerson)(uid=%s))',
                                      'admin_filter': '(objectClass=inetOrgPerson)',
                                      'attribute_username': '',
                                      'attribute_name': 'name',
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


def extract_csrf(reaponse):
    soup = BeautifulSoup(reaponse, "html.parser")
    return soup.find_all('meta', {'name': '_csrf'})[0]['content']


def remove():
    app = api.get_app_setup(APP_NAME)

    app.remove_service(SYSTEMD_GOGS)
    app.remove_service(SYSTEMD_POSTGRESQL)

    app_dir = app.get_install_dir()

    fs.removepath(app_dir)


def prepare_storage():
    app = api.get_app_setup(APP_NAME)
    app_storage_dir = app.init_storage(USER_NAME)