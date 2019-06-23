import os
import shutil
from os.path import dirname, join
from subprocess import check_output

import pytest
import requests
from bs4 import BeautifulSoup
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install, wait_for_rest, wait_for_installer

DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def module_setup(request, app_domain, data_dir, platform_data_dir, app_dir, device, log_dir):
    request.addfinalizer(lambda: module_teardown(app_domain, data_dir, platform_data_dir, app_dir, device, log_dir))


def module_teardown(app_domain, data_dir, platform_data_dir, app_dir, device, log_dir):
    platform_log_dir = join(log_dir, 'platform')
    os.mkdir(platform_log_dir)
    device.scp_from_device('{0}/log/*'.format(platform_data_dir), platform_log_dir)
  
    device.run_ssh('ls -la {0}'.format(data_dir), throw=False)
    device.run_ssh('cat {0}/config/gogs.ini'.format(app_dir), throw=False)
    device.run_ssh('{0}/git/bin/git config --global user.name'.format(app_dir), env_vars='HOME=/home/git', throw=False)
    device.run_ssh('{0}/git/bin/git config --global user.email'.format(app_dir), env_vars='HOME=/home/git', throw=False)

    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)
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
  
    app_log_dir = join(log_dir, 'app')
    os.mkdir(app_log_dir)
    device.scp_from_device('{0}/log/*.log'.format(data_dir), app_log_dir)
    device.scp_from_device('{0}/*.log'.format(TMP_DIR), app_log_dir)
    

@pytest.fixture(scope='function')
def gogs_session(app_domain, device_user, device_password):
    session = requests.session()
    main_response = session.get('https://{0}/user/login'.format(app_domain), allow_redirects=False, verify=False)
    soup = BeautifulSoup(main_response.text, "html.parser")
    csrf = soup.find_all('meta', {'name': '_csrf'})[0]['content']
    login_response = session.post('https://{0}/user/login'.format(app_domain),
                                  data={'user_name': device_user, 'password': device_password, '_csrf': csrf},
                                  allow_redirects=False, verify=False)
                               
    assert login_response.status_code == 302, login_response.text
    return session


def test_start(module_setup, device_host, log_dir, app, device):
    shutil.rmtree(log_dir, ignore_errors=True)
    os.mkdir(log_dir)
    add_host_alias(app, device_host)
    print(check_output('date', shell=True))
    device.run_ssh('date', retries=20)



def test_activate_device(app_domain, domain, main_domain, device):

    response = device.activate()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)


def test_storage_dir(device):
    device.run_ssh('ls -la /data/gogs')


def test_git_config(device, app_dir):
    device.run_ssh('{0}/git/bin/git config -l'.format(app_dir), env_vars='HOME=/home/git')


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


def test_remove(device_session, device_host):
    response = device_session.get('https://{0}/rest/remove?app_id=gogs'.format(device_host),
                                    allow_redirects=False, verify=False)
    assert response.status_code == 200, response.text
    wait_for_installer(device_session, device_host)


def test_reinstall(app_archive_path, app_domain, device_password):
    local_install(app_domain, device_password, app_archive_path)

