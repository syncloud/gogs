import json
import os
import sys
from os import listdir
from os.path import dirname, join, exists, abspath, isdir
import time
from subprocess import check_output
import pytest
import shutil

from integration.util.loop import loop_device_add, loop_device_cleanup
from integration.util.ssh import run_scp, ssh_command, SSH, run_ssh
import requests
from bs4 import BeautifulSoup

SYNCLOUD_INFO = 'syncloud.info'
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')


@pytest.fixture(scope="session")
def module_setup(request):
    request.addfinalizer(module_teardown)


def module_teardown():
    os.mkdir(LOG_DIR)
    platform_log_dir = join(LOG_DIR, 'platform')
    os.mkdir(platform_log_dir)
    run_scp('root@localhost:/opt/data/platform/log/* {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)
    nextcloud_log_dir = join(LOG_DIR, 'app')
    os.mkdir(nextcloud_log_dir)
    run_scp('root@localhost:/opt/data/gogs/log/*.log {0}'.format(nextcloud_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    run_scp('root@localhost:/var/log/sam.log {0}'.format(platform_log_dir), password=LOGS_SSH_PASSWORD)

    print('systemd logs')
    run_ssh('journalctl | tail -200', password=LOGS_SSH_PASSWORD)

    print('-------------------------------------------------------')
    print('syncloud docker image is running')
    print('connect using: {0}'.format(ssh_command(DEVICE_PASSWORD, SSH)))
    print('-------------------------------------------------------')


@pytest.fixture(scope='function')
def syncloud_session():
    session = requests.session()
    session.post('http://localhost/rest/login', data={'name': DEVICE_USER, 'password': DEVICE_PASSWORD})
    return session


@pytest.fixture(scope='function')
def gogs_session(user_domain):
    session = requests.session()
    response = session.get('http://127.0.0.1/index.php/login', headers={"Host": user_domain}, allow_redirects=False)
    soup = BeautifulSoup(response.text, "html.parser")
    requesttoken = soup.find_all('input', {'name': 'requesttoken'})[0]['value']
    response = session.post('http://127.0.0.1/index.php/login',
                            headers={"Host": user_domain},
                            data={'user': DEVICE_USER, 'password': DEVICE_PASSWORD, 'requesttoken': requesttoken},
                            allow_redirects=False)
    assert response.status_code == 303, response.text
    return session, requesttoken


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)


def test_activate_device(auth):
    email, password, domain, release, _= auth

    run_ssh('/opt/app/sam/bin/sam update --release {0}'.format(release), password=DEFAULT_DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug upgrade platform', password=DEFAULT_DEVICE_PASSWORD)

    response = requests.post('http://localhost:81/rest/activate',
                             data={'main_domain': SYNCLOUD_INFO, 'redirect_email': email, 'redirect_password': password,
                                   'user_domain': domain, 'device_username': DEVICE_USER, 'device_password': DEVICE_PASSWORD})
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_install(app_archive_path):
    __local_install(app_archive_path)


def test_storage_dir():
    run_ssh('ls -la /data/gogs', password=DEVICE_PASSWORD)


def test_remove(syncloud_session):
    response = syncloud_session.get('http://localhost/rest/remove?app_id=gogs', allow_redirects=False)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path):
    __local_install(app_archive_path)


def __local_install(app_archive_path):
    run_scp('{0} root@localhost:/app.tar.gz'.format(app_archive_path), password=DEVICE_PASSWORD)
    run_ssh('/opt/app/sam/bin/sam --debug install /app.tar.gz', password=DEVICE_PASSWORD)
    time.sleep(3)
