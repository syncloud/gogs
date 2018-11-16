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

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'gogs_user@syncloud.info'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'gogs_log')
screenshot_dir = join(DIR, 'screenshot')


@pytest.fixture(scope="module")
def driver():

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '/tools/firefox/firefox'
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('/tools/firefox/JSErrorCollector.xpi')
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile, capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                               firefox_binary=binary, executable_path=join(DIR, '/tools/geckodriver/geckodriver'))

    desktop_w = 1280
    desktop_h = 2000
    driver.set_window_position(0, 0)
    driver.set_window_size(desktop_w, desktop_h)

    return driver


def test_login(app_domain, driver):

    driver.get("https://{0}".format(app_domain))

    # print(driver.page_source.encode("utf-8"))

    user = driver.find_element_by_id("user_name")
    user.send_keys(DEVICE_USER)
    password = driver.find_element_by_id("password")
    password.send_keys(DEVICE_PASSWORD)
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))
    password.send_keys(Keys.RETURN)

    time.sleep(2)
    driver.get_screenshot_as_file(join(screenshot_dir, 'main.png'))

    # print(driver.page_source.encode("utf-8"))


def test_users(app_domain, driver):

    driver.get("https://{0}/admin/users".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.blue')))

    driver.get_screenshot_as_file(join(screenshot_dir, 'users.png'))


def test_user(app_domain, driver):

    driver.get("https://{0}/admin/users/2".format(app_domain))
    print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    driver.get_screenshot_as_file(join(screenshot_dir, 'user.png'))


def test_create_repo_empty(app_domain, driver):

    driver.get("https://{0}/repo/create".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('empty')
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-create-empty.png'))

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-empty.png'))
    # print(driver.page_source.encode("utf-8"))


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
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-create-init.png'))

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-init.png'))
    # print(driver.page_source.encode("utf-8"))


def test_ldap_auth(app_domain, driver):

    driver.get("https://{0}/admin/auths/1".format(app_domain))
    # print(driver.page_source.encode("utf-8"))
    # time.sleep(5)
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    driver.get_screenshot_as_file(join(screenshot_dir, 'ldap-auth.png'))
