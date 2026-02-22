from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

UPGRADE_REPO = 'upgrade-test'


def login(selenium, device_user, device_password):

    selenium.open_app()
    user = selenium.find_by_id("user_name")
    user.send_keys(device_user)
    password = selenium.find_by_id("password")
    password.send_keys(device_password)
    selenium.screenshot('login.png')
    password.send_keys(Keys.RETURN)

    time.sleep(2)
    selenium.screenshot('main')


def create_repo(selenium, device_user):
    selenium.find_by_xpath("//i[@class='octicon octicon-plus']").click()
    selenium.find_by_xpath("//a[contains(.,'New Repository')]").click()
    selenium.find_by_id("repo_name").send_keys(UPGRADE_REPO)
    selenium.find_by_id("auto-init").click()
    selenium.screenshot('upgrade-create-repo')
    selenium.find_by_xpath("//button[contains(.,'Create Repository')]").click()
    selenium.screenshot('upgrade-repo-created')


def web_edit_readme(selenium, device_user, content, mode):
    selenium.find_by_xpath("//a[contains(.,'Dashboard')]").click()
    selenium.find_by_xpath("//a[@href='/{0}/{1}']".format(device_user, UPGRADE_REPO)).click()
    selenium.find_by_xpath("//a[@href='/{0}/{1}/src/master/README.md']".format(device_user, UPGRADE_REPO)).click()
    selenium.find_by_xpath("//a[@href='/{0}/{1}/_edit/master/README.md']".format(device_user, UPGRADE_REPO)).click()
    edit = selenium.find_by_css(".CodeMirror")
    selenium.driver.execute_script("arguments[0].CodeMirror.setValue(arguments[1]);", edit, content)
    selenium.screenshot('upgrade-{0}-web-edit'.format(mode))
    selenium.find_by_css("button.ui").click()
    selenium.screenshot('upgrade-{0}-web-commit'.format(mode))


def check_readme_content(selenium, device_user, content):
    selenium.find_by_xpath("//a[contains(.,'Dashboard')]").click()
    selenium.find_by_xpath("//a[@href='/{0}/{1}']".format(device_user, UPGRADE_REPO)).click()
    selenium.find_by_xpath("//*[contains(text(),'{0}')]".format(content))
    selenium.screenshot('upgrade-check-content')
