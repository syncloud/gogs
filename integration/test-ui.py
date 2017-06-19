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
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'gogs_log')
screenshot_dir = join(DIR, 'screenshot')


@pytest.fixture(scope="module")
def driver():

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '{0}/firefox/firefox'.format(DIR)
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('{0}/JSErrorCollector.xpi'.format(DIR))
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile, capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                               firefox_binary=binary, executable_path=join(DIR, 'geckodriver/geckodriver'))
    #driver.set_page_load_timeout(30)
    #print driver.capabilities['version']
    return driver


def test_login(user_domain, driver):

    driver.get("http://{0}".format(user_domain))
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))

    print(driver.page_source.encode("utf-8"))

    user = driver.find_element_by_id("user_name")
    user.send_keys('gogs')
    password = driver.find_element_by_id("password")
    password.send_keys('gogs')
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))
    password.send_keys(Keys.RETURN)

    wait_driver = WebDriverWait(driver, 10)
    #wait_driver.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#header #expandDisplayName'), DEVICE_USER))

    #wait_driver.until(EC.element_to_be_clickable((By.ID, 'closeWizard')))
    #wizard_close_button = driver.find_element_by_id("closeWizard")
    #wizard_close_button.click()

    time.sleep(2)
    driver.get_screenshot_as_file(join(screenshot_dir, 'main.png'))

    print(driver.page_source.encode("utf-8"))


def test_create_repo_empty(user_domain, driver):

    driver.get("http://{0}/repo/create".format(user_domain))
    print(driver.page_source.encode("utf-8"))
    # time.sleep(5)
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('empty')
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-create-empty.png'))

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-empty.png'))
    print(driver.page_source.encode("utf-8"))


def test_create_repo_init(user_domain, driver):

    driver.get("http://{0}/repo/create".format(user_domain))
    print(driver.page_source.encode("utf-8"))
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
    print(driver.page_source.encode("utf-8"))