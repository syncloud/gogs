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
from syncloudlib.integration.screenshots import screenshots

DIR = dirname(__file__)
screenshot_dir = join(DIR, 'screenshot')
TMP_DIR = '/tmp/syncloud/ui'

@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode):
    request.addfinalizer(lambda: module_teardown(device, log_dir, ui_mode))


def module_teardown(device, log_dir, ui_mode):
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
    device.run_ssh('journalctl > {0}/journalctl.ui.{1} log'.format(TMP_DIR, ui_mode), throw=False)
    device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
      
    device.scp_from_device('{0}/*'.format(TMP_DIR), join(log_dir, 'log'))


def test_login(app_domain, driver, device_user, device_password):

    driver.get("https://{0}".format(app_domain))

    user = driver.find_element_by_id("user_name")
    user.send_keys(device_user)
    password = driver.find_element_by_id("password")
    password.send_keys(device_password)
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))
    password.send_keys(Keys.RETURN)

    time.sleep(2)
    screenshots(driver, screenshot_dir, 'main-' + ui_mode)


def test_users(app_domain, driver):

    driver.get("https://{0}/admin/users".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 100)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.blue')))

    screenshots(driver, screenshot_dir, 'users-' + ui_mode)


def test_user(app_domain, driver):

    driver.get("https://{0}/admin/users/2".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    screenshots(driver, screenshot_dir, 'user-' + ui_mode)


def test_create_repo_empty(app_domain, driver):

    driver.get("https://{0}/repo/create".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('empty')
    screenshots(driver, screenshot_dir, 'repo-create-empty-' + ui_mode)

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    screenshots(driver, screenshot_dir, 'repo-empty-' + ui_mode)


def test_create_repo_init(app_domain, driver):

    driver.get("https://{0}/repo/create".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    # time.sleep(5)
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('init')

    auto_init = driver.find_element_by_name("auto_init")
    auto_init.click()
    screenshots(driver, screenshot_dir, 'repo-create-init-' + ui_mode)

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    screenshots(driver, screenshot_dir, 'repo-init-' + ui_mode)


def test_web_commit(app_domain, driver):

    driver.get("https://{0}/gogs_user/init/_edit/master/README.md".format(app_domain))
    
    time.sleep(5)
    
    print(driver.page_source.encode("utf-8"))
    edit = driver.find_element_by_css_selector(".CodeMirror-code")
    edit.click()
    edit.send_keys('test 123')
    screenshots(driver, screenshot_dir, 'web-edit-' + ui_mode)

    driver.find_element_by_css_selector("button.ui").click()
    time.sleep(5)
    screenshots(driver, screenshot_dir, 'web-commit-' + ui_mode)

def test_ldap_auth(app_domain, driver):

    driver.get("https://{0}/admin/auths/1".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    # time.sleep(5)
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    screenshots(driver, screenshot_dir, 'ldap-auth-' + ui_mode)
