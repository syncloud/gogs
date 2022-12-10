import logging
import shutil
import time
import uuid
from os import path
from os.path import isdir, join
from subprocess import check_output

import requests_unixsocket
from bs4 import BeautifulSoup
from syncloudlib import fs, linux, gen, logger
from syncloudlib.application import paths, urls, storage, users

from database import Database

APP_NAME = 'gogs'
USER_NAME = 'git'
SYSTEMD_GOGS = 'gogs'
SYSTEMD_POSTGRESQL = 'gogs-postgresql'
PSQL_PATH = 'postgresql/bin/psql.sh'
PSQL_DATA_PATH = 'database'
PSQL_PORT = 5433
DB_USER = 'git'
DB_PASS = 'git'
DB_NAME = 'gogs'
GOGS_ADMIN_USER = 'gogs'
GOGS_ADMIN_PASSWORD = uuid.uuid4().hex

logger.init(logging.DEBUG, console=True, line_format='%(message)s')

install_file = join(paths.get_data_dir(APP_NAME), 'installed')


class Installer:
    def __init__(self):
        self.app_dir = paths.get_app_dir(APP_NAME)
        self.app_data_dir = paths.get_data_dir(APP_NAME)
        self.data_dir = join('/var/snap', APP_NAME, 'current')
        self.database_path = join(self.app_data_dir, PSQL_DATA_PATH)
        self.log = logger.get_logger('gogs')
        socket = '{0}/web.socket'.format(self.app_data_dir).replace('/', '%2F')
        self.base_url = 'http+unix://{0}'.format(socket)
        self.config_dir = join(self.data_dir, 'config')
        self.db = Database(self.app_dir, self.data_dir, self.config_dir, join(self.app_dir, PSQL_PATH), DB_USER, self.database_path, PSQL_PORT)

    def init_config(self):
        home_folder = join('/home', USER_NAME)
        linux.useradd(USER_NAME, home_folder=home_folder, shell='/bin/bash')
        log_path = join(self.app_data_dir, 'log')
        fs.makepath(log_path)
        gogs_repos_path = storage.init_storage(APP_NAME, USER_NAME)
        variables = {
            'app_dir': self.app_dir,
            'app_data_dir': self.app_data_dir,
            'database_dir': self.database_path,
            'db_psql_port': PSQL_PORT,
            'db_name': DB_NAME,
            'db_user': DB_USER,
            'db_password': DB_PASS,
            'gogs_repos_path': gogs_repos_path,
            'log_path': log_path,
            'app_url': urls.get_app_url(APP_NAME),
            'app_domain': urls.get_app_domain_name(APP_NAME),
            'web_secret': uuid.uuid4().hex,
            'disable_registration': False
        }
        templates_path = join(self.app_dir, 'config')
        gen.generate_files(templates_path, self.config_dir, variables)
        fs.chownpath(self.app_data_dir, USER_NAME, recursive=True)
        fs.chownpath(self.data_dir, USER_NAME, recursive=True)

    def install(self):
        self.init_config()
        self.db.init()
        self.db.init_config()

    def pre_refresh(self):
        self.db.backup()

    def post_refresh(self):
        self.log.info('post refresh')
        self.init_config()
        if self.db.requires_upgrade():
            self.db.remove()
            self.db.init()
        self.db.init_config()

    def installed(self):
        return path.isfile(install_file)

    def configure(self):
        self.log.info('configure')
        if self.installed():
            self.upgrade()
        else:
            self.initialize()

    def upgrade(self):
        self.log.info('upgrade')
        if self.db.requires_upgrade():
            self.log.info('db requires an upgrade, restoring db')
            self.db.restore()

    def initialize(self):
        self.log.info('initialize')

        self.log.info('creating database')
        self.db.execute('postgres', "ALTER USER {0} WITH PASSWORD '{1}';".format(DB_USER, DB_PASS))
        self.db.execute('postgres', "CREATE DATABASE {0} WITH OWNER={1};".format(DB_NAME, DB_USER))

        self.create_install_user(users.get_email(), GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
        self.activate_ldap(GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
        self.delete_install_user(GOGS_ADMIN_USER, GOGS_ADMIN_PASSWORD)
        self.db.execute(DB_NAME, "select * from login_source;")
        with open(install_file, 'w') as f:
            f.write('installed\n')

    def create_install_user(self, email, login, password):
        signup_url = '{0}/user/sign_up'.format(self.base_url)

        self.wait_url(self.base_url, timeout=60)

        self.log.info("Creating an install user, email: {0} url: {1}".format(email, signup_url))
        session = requests_unixsocket.Session()
        response = session.post(signup_url, allow_redirects=False, timeout=120, data={
            'user_name': login,
            'password': password,
            'retype': password,
            'email': email
        })

        if response.status_code != 302:
            self.log.error('failed with status code: {0}'.format(response.status_code))
            self.log.error(response.text.encode("utf-8"))
            raise Exception('unable to create install user')
        else:
            self.log.info('install user created')

    def delete_install_user(self, username, password):
        self.log.info('getting csrf to delete install user')
        session = self.gogs_login(username, password)
        url = '{0}/admin/users/1'.format(self.base_url)
        csrf = self.extract_csrf(session, url)

        url = '{0}/admin/users/1/delete'.format(self.base_url)
        self.log.info('deleting install user')
        response = session.post(url, allow_redirects=False,
                                data={'id': 1, '_csrf': csrf})

        if response.status_code != 200:
            self.log.error('status code: {0}'.format(response.status_code))
            self.log.error(response.text.encode("utf-8"))
            raise Exception('unable to delete install user')

    def gogs_login(self, username, password):
        self.wait_url(self.base_url, timeout=60)

        session = requests_unixsocket.Session()

        login_url = '{0}/user/login'.format(self.base_url)
        login_csrf = self.extract_csrf(session, login_url)

        response = session.post(login_url,
                                data={'user_name': username, 'password': password,
                                      '_csrf': login_csrf},
                                allow_redirects=False)

        if response.status_code != 302:
            self.log.error('status code: {0}'.format(response.status_code))
            self.log.error(response.text.encode("utf-8"))
            raise Exception('unable to login')

        return session

    def activate_ldap(self, username, password):
        self.log.info('activating ldap')
        session = self.gogs_login(username, password)

        auth_url = '{0}/admin/auths/new'.format(self.base_url)
        auth_csrf = self.extract_csrf(session, auth_url)

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
                                         'filter': '(&(objectclass=inetOrgPerson)(cn=%s))',
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
                                         'is_default': 'on',
                                         'is_active': 'on'},
                                     allow_redirects=False)

        if auth_response.status_code != 302:
            self.log.error('status code: {0}'.format(auth_response.status_code))
            self.log.error(auth_response.text.encode("utf-8"))
            raise Exception('unable to enable ldap')

    def extract_csrf(self, session, url):
        self.log.info('extract_csrf')
        response = session.get(url)
        code = response.status_code
        if code != 200:
            self.log.error('url: {0}'.format(url))
            self.log.error('status code: {0}'.format(code))
            self.log.error(response.text.encode("utf-8"))
            raise Exception('unable to get csrf')

        soup = BeautifulSoup(response.text, "html.parser")

        self.log.info(response)
        found = soup.find_all('meta', {'name': '_csrf'})
        self.log.info('found: {0}'.format(found))
        first = found[0]
        self.log.info('first: {0}'.format(first))
        return first['content']

    def prepare_storage(self):
        storage.init_storage(APP_NAME, USER_NAME)

    def on_domain_change(self):
        self.log.info('domain change')
        self.init_config()

    def wait_url(self, url, timeout, interval=3):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                session = requests_unixsocket.Session()
                self.log.info('waiting for url: {0}'.format(url))
                response = session.get(url, allow_redirects=False)
                if response.status_code == 200 or response.status_code == 302:
                    return
                self.log.info(response.status_code)
            except Exception as e:
                self.log.info(str(e))
            time.sleep(interval)
        raise Exception('Timeout waiting for url: {0}'.format(url))

