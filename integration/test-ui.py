from os.path import dirname, join

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from syncloudlib.integration.hosts import add_host_alias

from integration import lib

DIR = dirname(__file__)
screenshot_dir = join(DIR, 'screenshot')
TMP_DIR = '/tmp/syncloud/ui'


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode):
    request.addfinalizer(lambda: module_teardown(device, log_dir, ui_mode))


def module_teardown(device, log_dir, ui_mode):
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
    device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
    device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
      
    device.scp_from_device('{0}/*'.format(TMP_DIR), join(log_dir, 'log'))


def test_start(module_setup, app, domain, device_host):
    add_host_alias(app, device_host, domain)


def test_login(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)

    
def test_users(selenium):
    # driver.get("https://{0}/admin/users".format(app_domain))
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.CSS_SELECTOR, '.blue')))
    selenium.screenshot('users')


def test_user(selenium):

    # driver.get("https://{0}/admin/users/2".format(app_domain))
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))
    selenium.screenshot('user')


def test_create_repo_empty(selenium):

    # driver.get("https://{0}/repo/create".format(app_domain))
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))
    name = selenium.find_by_id("repo_name")
    name.send_keys('empty')
    selenium.screenshot('repo-create-empty')
    create = selenium.find_by_css_selector(".green")
    create.click()
    selenium.screenshot('repo-empty')


def test_create_repo_init(selenium):

    # driver.get("https://{0}/repo/create".format(app_domain))
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = selenium.find_by_id("repo_name")
    name.send_keys('init')
    description = selenium.find_by_id("description")
    description.send_keys('description')

    selenium.screenshot('repo-create-init')

    selenium.wait_or_screenshot(EC.presence_of_element_located((By.ID, 'auto-init')))
    auto_init = selenium.find_by_id("auto-init")
    auto_init.click()
    selenium.screenshot('repo-create-init')

    selenium.wait_or_screenshot(EC.presence_of_element_located((By.CSS_SELECTOR, '.green')))
    create = selenium.find_by_css_selector(".green")
    create.click()

    selenium.screenshot('repo-init')


def test_web_commit(selenium):

    # driver.get("https://{0}/{1}/init/_edit/master/README.md".format(app_domain, device_user))

    selenium.screenshot('web-edit')

    edit = selenium.find_by_css_selector(".CodeMirror")
    selenium.driver.execute_script("arguments[0].CodeMirror.setValue(\"test 123\");", edit)

    selenium.screenshot('web-edit')

    selenium.find_by_css_selector("button.ui").click()
    selenium.screenshot('web-commit')


def test_ldap_auth(selenium):

    # driver.get("https://{0}/admin/auths/1".format(app_domain))
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    selenium.screenshot('ldap-auth')
