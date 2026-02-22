import pytest
from subprocess import check_output, CalledProcessError, STDOUT
from syncloudlib.integration.hosts import add_host_alias
from test import lib
from syncloudlib.integration.installer import local_install, wait_for_installer
from syncloudlib.http import wait_for_rest
import requests

TMP_DIR = '/tmp/syncloud'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('journalctl > {0}/refresh.journalctl.log'.format(TMP_DIR), throw=False)
        device.run_ssh('cp /var/snap/gogs/current/database.dump {0}'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        check_output('cp /videos/* {0} || true'.format(artifact_dir), shell=True)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, device_host, domain, device):
    add_host_alias(app, device_host, domain)
    device.activated()
    device.run_ssh('rm -rf {0}'.format(TMP_DIR), throw=False)
    device.run_ssh('mkdir {0}'.format(TMP_DIR), throw=False)


def test_install_from_store(device, app_domain):
    device.run_ssh('snap remove gogs')
    device.run_ssh('snap install gogs', retries=10)
    device.run_ssh('test -f /var/snap/gogs/common/installed', retries=100)
    wait_for_rest(requests.session(), "https://{0}".format(app_domain), 200, 100)


def test_login_pre_upgrade(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)


def test_create_repo(selenium, device_user):
    lib.create_repo(selenium, device_user)


def test_edit_readme_pre_upgrade(selenium, device_user):
    lib.web_edit_readme(selenium, device_user, 'pre-upgrade content', 'pre')


def test_upgrade(device_host, device_password, app_archive_path, app_domain):
    local_install(device_host, device_password, app_archive_path)
    wait_for_rest(requests.session(), "https://{0}".format(app_domain), 200, 100)


def test_login_post_upgrade(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)


def test_check_pre_upgrade_data(selenium, device_user):
    lib.check_readme_content(selenium, device_user, 'pre-upgrade content')


def test_edit_readme_post_upgrade(selenium, device_user):
    lib.web_edit_readme(selenium, device_user, 'post-upgrade content', 'post')
