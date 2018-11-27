import os
import shutil
from os.path import dirname, join

import pytest
import requests
from bs4 import BeautifulSoup
from syncloudlib.integration.installer import local_install, get_data_dir, get_app_dir, get_service_prefix, wait_for_sam
from syncloudlib.integration.ssh import run_scp, run_ssh

DEVICE_USER = 'gogs_user@syncloud.info'
DEVICE_PASSWORD = 'password'
DEFAULT_DEVICE_PASSWORD = 'syncloud'
LOGS_SSH_PASSWORD = DEFAULT_DEVICE_PASSWORD
DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
TMP_DIR = '/tmp/syncloud'
REDIRECT_USER = "teamcity@syncloud.it"
REDIRECT_PASSWORD = "password"


@pytest.fixture(scope="session")
def platform_data_dir():
    return get_data_dir('platform')

    
@pytest.fixture(scope="session")
def data_dir():
    return get_data_dir('gogs')


@pytest.fixture(scope="session")
def app_dir():
    return get_app_dir('gogs')
    

@pytest.fixture(scope="session")
def service_prefix():
    return get_service_prefix()


@pytest.fixture(scope="session")
def module_setup(request, app_domain, data_dir, platform_data_dir, app_dir, service_prefix):
    request.addfinalizer(lambda: module_teardown(app_domain, data_dir, platform_data_dir, app_dir, service_prefix))


def module_teardown(app_domain, data_dir, platform_data_dir, app_dir, service_prefix):
    platform_log_dir = join(LOG_DIR, 'platform')
    os.mkdir(platform_log_dir)
    run_scp('root@{0}:{1}/log/* {2}'.format(app_domain, platform_data_dir, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    app_log_dir = join(LOG_DIR, 'app')
    os.mkdir(app_log_dir)
    run_scp('root@{0}:{1}/log/*.log {2}'.format(app_domain, data_dir, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    run_scp('root@{0}:/var/log/sam.log {1}'.format(app_domain, platform_log_dir), password=LOGS_SSH_PASSWORD, throw=False)

    run_ssh(app_domain, 'ls -la {0}'.format(data_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'cat {0}/config/gogs.ini'.format(app_dir), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, '{0}/git/bin/git config --global user.name'.format(app_dir), password=LOGS_SSH_PASSWORD, throw=False, env_vars='HOME=/home/git')
    run_ssh(app_domain, '{0}/git/bin/git config --global user.email'.format(app_dir), password=LOGS_SSH_PASSWORD, throw=False, env_vars='HOME=/home/git')

    run_ssh(app_domain, 'mkdir {0}'.format(TMP_DIR), password=LOGS_SSH_PASSWORD)
    run_ssh(app_domain, 'top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'ps auxfw > {0}/ps.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'systemctl status {0}gogs > {1}/gogs.status.log'.format(service_prefix, TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'netstat -nlp > {0}/netstat.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'journalctl | tail -500 > {0}/journalctl.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'tail -500 /var/log/syslog > {0}/syslog.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)
    run_ssh(app_domain, 'tail -500 /var/log/messages > {0}/messages.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /snap/gogs > {0}/snap.gogs.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /var/snap > {0}/var.snap.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /var/snap/gogs > {0}/var.snap.gogs.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /var/snap/gogs/common > {0}/var.snap.gogs.common.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /data > {0}/data.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_ssh(app_domain, 'ls -la /data/gogs > {0}/data.gogs.ls.log'.format(TMP_DIR), password=LOGS_SSH_PASSWORD, throw=False)    
    run_scp('root@{0}:{1}/*.log {2}'.format(app_domain, TMP_DIR, app_log_dir), password=LOGS_SSH_PASSWORD, throw=False)
    

@pytest.fixture(scope='function')
def syncloud_session(device_host):
    session = requests.session()
    session.post('https://{0}/rest/login'.format(device_host),
                 data={'name': DEVICE_USER, 
                       'password': DEVICE_PASSWORD},
                 verify=False)
    return session


@pytest.fixture(scope='function')
def gogs_session(app_domain):
    session = requests.session()
    main_response = session.get('https://{0}/user/login'.format(app_domain), allow_redirects=False, verify=False)
    soup = BeautifulSoup(main_response.text, "html.parser")
    csrf = soup.find_all('meta', {'name': '_csrf'})[0]['content']
    login_response = session.post('https://{0}/user/login'.format(app_domain),
                                  data={'user_name': DEVICE_USER, 'password': DEVICE_PASSWORD, '_csrf': csrf},
                                  allow_redirects=False, verify=False)
                               
    assert login_response.status_code == 302, login_response.text
    return session


def test_start(module_setup):
    shutil.rmtree(LOG_DIR, ignore_errors=True)
    os.mkdir(LOG_DIR)


def test_activate_device(app_domain, domain, main_domain):

    response = requests.post('http://{0}:81/rest/activate'.format(app_domain),
                             data={'main_domain': main_domain,
                                   'redirect_email': REDIRECT_USER,
                                   'redirect_password': REDIRECT_PASSWORD,
                                   'user_domain': domain,
                                   'device_username': DEVICE_USER,
                                   'device_password': DEVICE_PASSWORD},
                                   verify=False)
    assert response.status_code == 200, response.text
    global LOGS_SSH_PASSWORD
    LOGS_SSH_PASSWORD = DEVICE_PASSWORD


def test_install(app_archive_path, app_domain):
    local_install(app_domain, DEVICE_PASSWORD, app_archive_path)


def test_storage_dir(app_domain):
    run_ssh(app_domain, 'ls -la /data/gogs', password=DEVICE_PASSWORD)


def test_git_config(app_domain, app_dir):
    run_ssh(app_domain, '{0}/git/bin/git config -l'.format(app_dir), password=DEVICE_PASSWORD, env_vars='HOME=/home/git')


def test_login(gogs_session):
    session = gogs_session
    #todo
    #assert response.status_code == 200, response.text


def test_install_user_disabled(app_domain):
    session = requests.session()
    main_response = session.get('https://{0}/user/login'.format(app_domain), allow_redirects=False, verify=False)
    soup = BeautifulSoup(main_response.text, "html.parser")
    csrf = soup.find_all('meta', {'name': '_csrf'})[0]['content']
    login_response = session.post('https://{0}/user/login'.format(app_domain),
                                  data={'user_name': 'gogs', 'password': 'gogs', '_csrf': csrf},
                                  allow_redirects=False, verify=False)
                               
    assert login_response.status_code != 302, login_response.text
    return session


def test_remove(syncloud_session, device_host):
    response = syncloud_session.get('https://{0}/rest/remove?app_id=gogs'.format(device_host),
                                    allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_sam(syncloud_session, device_host)


def test_reinstall(app_archive_path, app_domain):
    local_install(app_domain, DEVICE_PASSWORD, app_archive_path)

