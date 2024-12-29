#!.venv/bin/python

import time
import json
import random
import argparse

from helpers.selenium_management import start_driver, close_driver
from helpers.utils import validate_instagram_url, ACCOUNT_VALUE
import config
from robot import auth, account_follow, account_send_message, account_get_post_links, account_send_comment

def main(args):
    account_counter = 0
    
    # Аргументы
    links_num = args.links_num
    is_follow = args.is_follow
    is_message = args.is_message
    is_comment = args.is_comment
    
    # Список ссылок на аккаунты
    with open(config.ACCOUNT_LINKS_PATH, "r", encoding="utf-8") as file:
        accounts = file.read()
        accounts = accounts.split('\n')
    # Список шаблонов сообщений
    with open(config.MESSAGE_TEMPLATES_PATH, "r", encoding="utf-8") as file:
        messages = json.load(file)
    # Список шаблонов комментариев
    with open(config.COMMENT_TEMPLATES_PATH, "r", encoding="utf-8") as file:
        comments = json.load(file)
    # Список данных от аккаунтов
    with open(config.AUTH_DATA_PATH, "r", encoding="utf-8") as file:
        auth_data_list = json.load(file)

    # Запуск робота
    for auth_data in auth_data_list:
        driver = start_driver()
        username = auth_data.get('username')
        password = auth_data.get('password')
        if not username or not password:
            raise Exception(f'В элементе нет username: "{username}" или password: "{password}"')
        auth(driver=driver, username=username, password=password)

        for account_link in accounts[account_counter:account_counter+links_num]:
            print(f'account_counter: #{account_counter}')
            link_type = validate_instagram_url(account_link)
            if link_type != ACCOUNT_VALUE:
                print(f'Ссылка "{account_link}" является невалидной. Должна быть ссылка на аккаунт')
                continue
            print(f'Начал обработку аккаунта "{account_link}"')
            
            # Подписка на аккаунт
            if is_follow:
                account_follow(driver=driver, account_link=account_link)
                time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))
            # Отправка сообщения аккаунту
            if is_message:
                account_send_message(driver=driver, account_link=account_link, message=random.choice(messages))
                time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))
            # Парсинг постов и отправка комментария к первому посту
            if is_comment:
                post_links = account_get_post_links(driver=driver, account_link=account_link)
                account_send_comment(driver=driver, post_link=random.choice(post_links), comment=random.choice(comments))
                time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))
            
            account_counter += 1
            time.sleep(random.randrange(config.ACCOUNT_BREAK_MIN_TIME, config.ACCOUNT_BREAK_MAX_TIME))

        close_driver(driver=driver)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скрипт отправки сообщений")
    parser.add_argument(
        "--links-num", type=int, default=1, help="Количество обработок ссылок для каждого аккаунта"
    )
    parser.add_argument(
        "--is-follow", default=False, action="store_true", help="Нужно ли подписываться на аккаунты"
    )
    parser.add_argument(
        "--is-message", default=False, action="store_true", help="Нужно ли писать сообщения аккаунтам"
    )
    parser.add_argument(
        "--is-comment", default=False, action="store_true", help="Нужно ли писать комментарий аккаунтам"
    )
    args = parser.parse_args()
    print(f'args: {args}')
    main(args=args)