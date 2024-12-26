#!.venv/bin/python

import json
import random
import argparse

from helpers.selenium_management import start_driver, close_driver
from helpers.utils import validate_instagram_url, ACCOUNT_VALUE
import config
from robot import auth, send_message_and_follow


def main(message_num):
    count = 0

    # Список ссылок на аккаунты
    with open(config.ACCOUNT_LINKS_PATH, "r", encoding="utf-8") as file:
        accounts = file.read()
        accounts = accounts.split('\n')

    # Список шаблонов сообщений
    with open(config.MESSAGE_TEMPLATES_PATH, "r", encoding="utf-8") as file:
        messages = json.load(file)

    # Список данных от аккаунтов
    with open(config.AUTH_DATA_PATH, "r", encoding="utf-8") as file:
        auth_data_list = json.load(file)

    for auth_data in auth_data_list:
        driver = start_driver()
        username = auth_data.get('username')
        password = auth_data.get('password')
        if not username or not password:
            raise Exception(f'В первом элементе нет username: "{username}" или password: "{password}"')
        auth(driver=driver, username=username, password=password)
        print(f'Аккаунт {username}')

        for account_link in accounts[count:count+message_num]:
            message = random.choice(messages)
            link_type = validate_instagram_url(account_link)
            if link_type != ACCOUNT_VALUE:
                raise Exception(f'Ссылка "{account_link}" является невалидной. Должна быть ссылка на аккаунт')
            send_message_and_follow(driver=driver, account_link=account_link, message=message)
            print(f'Отправил сообщение #{count} for account: {account_link}')
            count += 1

        close_driver(driver=driver)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скрипт отправки сообщений")
    parser.add_argument(
        "--message-num", type=int, default=1, help="Количество отправок сообщений для каждого аккаунта"
    )
    args = parser.parse_args()
    print(f'message num: {args.message_num}')
    main(args.message_num)