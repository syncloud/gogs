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

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'nextcloud_log')


@pytest.fixture(scope="session")
def driver():
    os.environ['PATH'] = os.environ['PATH'] + ":" + join(DIR, 'geckodriver')

    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps["binary"] = "/usr/bin/firefox"

    profile = webdriver.FirefoxProfile()
    profile.set_preference("webdriver.log.file", "{0}/firefox.log".format(log_dir))
    _driver=webdriver.Firefox(profile, capabilities=caps)
    _driver.maximize_window()
    return _driver


@pytest.fixture(scope="session")
def screenshot_dir():
    dir = join(DIR, 'screenshot')
    if exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)
    return dir


def test_login(user_domain, driver, screenshot_dir):

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


def test_create_repo(user_domain, driver, screenshot_dir):

    driver.get("http://{0}/repo/create".format(user_domain))
    print(driver.page_source.encode("utf-8"))
    # time.sleep(5)
    wait_driver = WebDriverWait(driver, 10)
    wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.green')))

    name = driver.find_element_by_id("repo_name")
    name.send_keys('gogs')
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-create.png'))

    create = driver.find_element_by_css_selector(".green")
    create.click()

    time.sleep(5)
    driver.get_screenshot_as_file(join(screenshot_dir, 'repo-create-result.png'))
    print(driver.page_source.encode("utf-8"))
