import os
import shutil
from os.path import dirname, join
from subprocess import check_output

import pytest
import requests
from bs4 import BeautifulSoup
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install, wait_for_installer
from requests.packages.urllib3.exceptions import InsecureRequestWarning

DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

@pytest.fixture(scope="session")
def module_setup(request, data_dir, platform_data_dir, app_dir, device, artifact_dir):
    def module_teardown():
        platform_log_dir = join(artifact_dir, 'platform')
        os.mkdir(platform_log_dir)
        device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)

        device.run_ssh('ls -la {0}'.format(data_dir), throw=False)
        device.run_ssh('cat {0}/config/gogs.ini'.format(app_dir), throw=False)
        device.run_ssh('{0}/git/bin/git config --global user.name'.format(app_dir), env_vars='HOME=/home/git', throw=False)
        device.run_ssh('{0}/git/bin/git config --global user.email'.format(app_dir), env_vars='HOME=/home/git', throw=False)

        device.run_ssh('top -bn 1 -w 500 -c > {0}/top.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ps auxfw > {0}/ps.log'.format(TMP_DIR), throw=False)
        device.run_ssh('systemctl status snap.gogs.* > {0}/gogs.status.log'.format(TMP_DIR), throw=False)
        device.run_ssh('netstat -nlp > {0}/netstat.log'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl | tail -500 > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/syslog > {0}/syslog.log'.format(TMP_DIR), throw=False)
        device.run_ssh('tail -500 /var/log/messages > {0}/messages.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap > {0}/snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /snap/gogs > {0}/snap.gogs.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap > {0}/var.snap.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/gogs > {0}/var.snap.gogs.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /var/snap/gogs/common > {0}/var.snap.gogs.common.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /data > {0}/data.ls.log'.format(TMP_DIR), throw=False)
        device.run_ssh('ls -la /data/gogs > {0}/data.gogs.ls.log'.format(TMP_DIR), throw=False)

        app_log_dir = join(artifact_dir, 'app')
        os.mkdir(app_log_dir)
        device.scp_from_device('{0}/log/*.log'.format(data_dir), app_log_dir)
        device.scp_from_device('{0}/*.log'.format(TMP_DIR), app_log_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, device, app, domain, device_host):
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100, throw=True)
    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)
        

def test_activate_device(device):
    response = device.activate_custom()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)


def test_storage_dir(device):
    device.run_ssh('ls -la /data/gogs')


def test_git_config(device, app_dir):
    device.run_ssh('{0}/git/bin/git config -l'.format(app_dir), env_vars='HOME=/home/git')


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


def test_storage_change_event(device):
    device.run_ssh('snap run gogs.storage-change > {0}/storage-change.log'.format(TMP_DIR))


def test_reinstall(app_archive_path, app_domain, device_password):
    local_install(app_domain, device_password, app_archive_path)
