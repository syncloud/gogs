import os
import shutil
from os.path import dirname, join, exists
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.screenshots import screenshots
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


def test_start(module_setup, app, device_host):
    if not exists(screenshot_dir):
        os.mkdir(screenshot_dir)

    add_host_alias(app, device_host)


def test_login(sepenium, device_user, device_password, ui_mode):
    lib.login(sepenium, device_user, device_password, ui_mode):

    
def test_users(app_domain, driver, ui_mode):

    driver.get("https://{0}/admin/users".format(app_domain))
    wait_driver = WebDriverWait(driver, 100)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.blue')))

    screenshots(driver, screenshot_dir, 'users-' + ui_mode)


def test_user(app_domain, driver, ui_mode):

    driver.get("https://{0}/admin/users/2".format(app_domain))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    screenshots(driver, screenshot_dir, 'user-' + ui_mode)


def test_create_repo_empty(app_domain, driver, ui_mode):

    driver.get("https://{0}/repo/create".format(app_domain))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('empty')
    screenshots(driver, screenshot_dir, 'repo-create-empty-' + ui_mode)

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    screenshots(driver, screenshot_dir, 'repo-empty-' + ui_mode)


def test_create_repo_init(app_domain, driver, ui_mode):

    driver.get("https://{0}/repo/create".format(app_domain))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('init')
    description = driver.find_element_by_id("description")
    description.send_keys('description')

    time.sleep(2)
    screenshots(driver, screenshot_dir, 'repo-create-init-' + ui_mode)

    wait_driver.until(EC.presence_of_element_located((By.ID, 'auto-init')))
    auto_init = driver.find_element_by_id("auto-init")
    auto_init.click()
    screenshots(driver, screenshot_dir, 'repo-create-init-' + ui_mode)

    wait_driver.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.green')))
    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    screenshots(driver, screenshot_dir, 'repo-init-' + ui_mode)


def test_web_commit(app_domain, driver, ui_mode, device_user):

    driver.get("https://{0}/{1}/init/_edit/master/README.md".format(app_domain, device_user))
    
    time.sleep(5)
    screenshots(driver, screenshot_dir, 'web-edit-' + ui_mode)

    edit = driver.find_element_by_css_selector(".CodeMirror")
    driver.execute_script("arguments[0].CodeMirror.setValue(\"test 123\");", edit);

    screenshots(driver, screenshot_dir, 'web-edit-' + ui_mode)

    driver.find_element_by_css_selector("button.ui").click()
    time.sleep(5)
    screenshots(driver, screenshot_dir, 'web-commit-' + ui_mode)

def test_ldap_auth(app_domain, driver, ui_mode):

    driver.get("https://{0}/admin/auths/1".format(app_domain))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    screenshots(driver, screenshot_dir, 'ldap-auth-' + ui_mode)
