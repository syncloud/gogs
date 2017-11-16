import os
import shutil
import time
from bs4 import BeautifulSoup
from os.path import dirname, join

import pytest
import requests

from integration.util.ssh import run_scp, run_ssh

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'gogs_user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')


@pytest.fixture(scope="session")
def module_setup(request, user_domain):
    request.addfinalizer(lambda: module_teardown(user_domain))


def module_teardown(user_domain):
    platform_log_dir = join(LOG_DIR, 'platform')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:/opt/data/platform/log/* {1}'.format(user_domain, platform_log_dir), password=LOGS_SSH_PASSWORD)
    app_log_dir = join(LOG_DIR, 'app')
    os.mkdir(app_log_dir)
    run_scp('root@{0}:/opt/data/gogs/log/*.log {1}'.format(user_domain, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    run_scp('root@{0}:/var/log/sam.log {1}'.format(user_domain, platform_log_dir), password=LOGS_SSH_PASSWORD)

    run_ssh(user_domain, 'ls -la /opt/data/gogs', password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(user_domain, 'cat /opt/data/gogs/config/gogs.ini', password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(user_domain, '/opt/app/gogs/git/bin/git config --global user.name', password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(user_domain, '/opt/app/gogs/git/bin/git config --global user.email', password=LOGS_SSH_PASSWORD, throw=False)


    print('systemd logs')
    run_ssh(user_domain, 'journalctl | tail -200', password=LOGS_SSH_PASSWORD)


@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('http://{0}/rest/login'.format(device_host), data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def gogs_session(user_domain):
    session = requests.session()
    main_response = session.get('http://{0}/user/login'.format(user_domain), allow_redirects=False)
    soup = BeautifulSoup(main_response.text, "html.parser")
    csrf = soup.find_all('meta', {'name': '_csrf'})[0]['content']
    login_response = session.post('http://{0}/user/login'.format(user_domain),
                                  data={'user_name': DEVICE_USER, 'password': DEVICE_PASSWORD, '_csrf': csrf},
                                  allow_redirects=False)
                               
    assert login_response.status_code == 302, login_response.text
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


def test_activate_device(auth, user_domain):
    email, password, domain, release = auth

    response = requests.post('http://{0}:81/rest/activate'.format(user_domain),
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_install(app_archive_path, user_domain):
    __local_install(app_archive_path, user_domain)


def test_storage_dir(user_domain):
    run_ssh(user_domain, 'ls -la /data/gogs', password=DEVICE_PASSWORD)


def test_git_config(user_domain, app_dir):
    run_ssh(user_domain, '{0}/git/bin/git config -l'.format(app_dir), password=DEVICE_PASSWORD)


def test_login(gogs_session):
    session = gogs_session
    #todo
    #assert response.status_code == 200, response.text


def test_install_user_disabled(user_domain):
    session = requests.session()
    main_response = session.get('http://{0}/user/login'.format(user_domain), allow_redirects=False)
    soup = BeautifulSoup(main_response.text, "html.parser")
    csrf = soup.find_all('meta', {'name': '_csrf'})[0]['content']
    login_response = session.post('http://{0}/user/login'.format(user_domain),
                                  data={'user_name': 'gogs', 'password': 'gogs', '_csrf': csrf},
                                  allow_redirects=False)
                               
    assert login_response.status_code != 302, login_response.text
    return session


def test_remove(syncloud_session, device_host):
    response = syncloud_session.get('http://{0}/rest/remove?app_id=gogs'.format(device_host), allow_redirects=False)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path, user_domain):
    __local_install(app_archive_path, user_domain)


def __local_install(app_archive_path, user_domain):
    run_scp('{0} root@{1}:/app.tar.gz'.format(app_archive_path, user_domain), password=DEVICE_PASSWORD)
    run_ssh(user_domain, '/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    time.sleep(3)
