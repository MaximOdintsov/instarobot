import json
import random

from helpers.selenium_management import start_driver, close_driver
import config
from robot import auth, send_message_and_follow


driver = start_driver()
auth(driver=driver, username='odintsovmaxim4@gmail.com', password='password1923DF!')



with open(config.MESSAGE_TEMPLATES_PATH, "r", encoding="utf-8") as file:
    messages = json.load(file)

accounts = ...  # Ограничить кол-во аккаунтов (через аргумент в cmd)
for account in accounts:
    message = random.choice(messages)
    send_message_and_follow(driver=driver, account_link=account.link, message=message)


close_driver()


