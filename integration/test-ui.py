from os.path import dirname, join

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from syncloudlib.integration.hosts import add_host_alias
from subprocess import check_output, CalledProcessError, STDOUT
from integration import lib

DIR = dirname(__file__)


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode, artifact_dir):
    def module_teardown():
        tmp_dir = '/tmp/syncloud/ui'
        device.activated()
        device.run_ssh('mkdir -p {0}/{1}'.format(tmp_dir, ui_mode), throw=False)
        device.run_ssh('journalctl > {0}/{1}/journalctl.log'.format(tmp_dir, ui_mode), throw=False)
        device.scp_from_device('{0}/*'.format(tmp_dir), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, domain, device_host):
    add_host_alias(app, device_host, domain)


def test_login(selenium, device_user, device_password):
    lib.login(selenium, device_user, device_password)

    
def test_users(selenium):
    # driver.get("https://{0}/admin/users".format(app_domain))
    selenium.find_by_xpath("//span[@class='text avatar']").click()
    selenium.find_by_xpath("//a[contains(.,'Admin Panel')]").click()
    selenium.find_by_xpath("//a[contains(.,'Users')]").click()
    selenium.find_by_xpath("//h4[contains(.,'User Manage Panel')]")
    selenium.screenshot('users')


def test_user(selenium):
    # driver.get("https://{0}/admin/users/2".format(app_domain))
    selenium.find_by_xpath("//a[@href='/admin/users/2']").click()
    selenium.find_by_xpath("//h4[contains(.,'Edit Account')]")
    selenium.screenshot('user')


def test_create_repo_empty(selenium):

    # driver.get("https://{0}/repo/create".format(app_domain))
    selenium.find_by_xpath("//i[@class='octicon octicon-plus']").click()
    selenium.find_by_xpath("//a[contains(.,'New Repository')]").click()
    selenium.find_by_id("repo_name").send_keys('empty')
    selenium.screenshot('repo-create-empty')
    selenium.find_by_xpath("//button[contains(.,'Create Repository')]").click()
    selenium.screenshot('repo-empty')


def test_create_repo_init(selenium):

    # driver.get("https://{0}/repo/create".format(app_domain))
    selenium.find_by_xpath("//i[@class='octicon octicon-plus']").click()
    selenium.find_by_xpath("//a[contains(.,'New Repository')]").click()
    selenium.find_by_id("repo_name").send_keys('init')
    description = selenium.find_by_id("description")
    description.send_keys('description')
    selenium.screenshot('repo-create-init')
    selenium.find_by_id("auto-init").click()
    selenium.screenshot('repo-create-init')
    selenium.find_by_xpath("//button[contains(.,'Create Repository')]").click()
    selenium.screenshot('repo-init')


def test_web_commit(selenium, device_user):

    # driver.get("https://{0}/{1}/init/_edit/master/README.md".format(app_domain, device_user))
    selenium.find_by_xpath("//a[contains(.,'Dashboard')]").click()
    selenium.find_by_xpath("//a[@href='/{0}/init']".format(device_user)).click()
    selenium.find_by_xpath("//a[@href='/{0}/init/src/master/README.md']".format(device_user)).click()
    selenium.find_by_xpath("//a[@href='/{0}/init/_edit/master/README.md']".format(device_user)).click()
    edit = selenium.find_by_css(".CodeMirror")
    selenium.driver.execute_script("arguments[0].CodeMirror.setValue(\"test 123\");", edit)
    selenium.screenshot('web-edit')
    selenium.find_by_css("button.ui").click()
    selenium.screenshot('web-commit')


def test_ldap_auth(selenium, device_user):

    # driver.get("https://{0}/admin/auths/1".format(app_domain))
    selenium.find_by_xpath("//span[@class='text avatar']").click()
    selenium.find_by_xpath("//a[contains(.,'Admin Panel')]").click()
    selenium.find_by_xpath("//a[contains(.,'Authentications')]").click()
    selenium.find_by_xpath("//a[@href='/admin/auths/1']".format(device_user)).click()
    selenium.find_by_xpath("//h4[contains(.,'Edit Authentication Setting')]")
    selenium.screenshot('ldap-auth')


def test_git_cli(device, device_user, device_password, device_host, app_archive_path, app_domain):
    run("git config --global http.sslverify false")
    run("git clone https://{0}:{1}@{2}/{3}/init init".format(device_user, device_password, app_domain, device_user))
    run("cd init; touch 1; git add .; git commit -am 'test'; git push;")

    
def test_teardown(driver):
    driver.quit()

def run(cmd):
    try:
        output = check_output(cmd, stderr=STDOUT, shell=True).decode()
        print(output)
    except CalledProcessError as e:
        print("error: " + e.output.decode())
        raise e
