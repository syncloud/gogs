from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


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
