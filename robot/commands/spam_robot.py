import click
import time
import json
import random

from robot.helpers.selenium_management import start_driver, close_driver
from robot.helpers.utils import validate_instagram_url, ACCOUNT_VALUE
from robot.robot import auth, account_follow, account_send_message, account_get_post_links, account_send_comment
from robot import config


def main(links_num, is_follow, is_message, is_comment):
    account_counter = 0

    if not is_follow and not is_message and not is_comment:
        print('Добавьте аргументы для робота! Например, --is-message')
        return

    # Список аккаунтов
    with open(config.ACCOUNT_LINKS_PATH, "r", encoding="utf-8") as file:
        all_links = file.read().split('\n')

    # Список сообщений
    with open(config.MESSAGE_TEMPLATES_PATH, "r", encoding="utf-8") as file:
        messages = json.load(file)

    # Список комментариев
    with open(config.COMMENT_TEMPLATES_PATH, "r", encoding="utf-8") as file:
        comments = json.load(file)

    # Список логинов/паролей
    with open(config.AUTH_DATA_PATH, "r", encoding="utf-8") as file:
        auth_data_list = json.load(file)

    # Запускаем бота по очереди для каждого аккаунта из AUTH_DATA_PATH
    for auth_data in auth_data_list:
        username = auth_data.get('username')
        password = auth_data.get('password')
        if not username or not password:
            raise Exception(f'Нет username: "{username}" или password: "{password}"')

        driver = start_driver()
        auth(driver=driver, username=username, password=password)

        # Обрабатываем следующие `links_num` аккаунтов из списка
        for account_link in all_links[account_counter : account_counter + links_num]:
            print(f'account_counter: #{account_counter}')
            link_type = validate_instagram_url(account_link)
            if link_type != ACCOUNT_VALUE:
                print(f'Ссылка "{account_link}" невалидна (ожидалась ссылка на аккаунт). Пропускаем.')
                continue

            print(f'Обработка аккаунта: {account_link}')

            # Подписка на аккаунт
            if is_follow:
                account_follow(driver=driver, account_link=account_link)
                time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))

            # Отправка сообщения
            if is_message:
                account_send_message(driver=driver, account_link=account_link, message=random.choice(messages))
                time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))

            # Парсинг постов и отправка комментария к первому посту
            if is_comment:
                post_links = account_get_post_links(driver=driver, account_link=account_link)
                if post_links:
                    account_send_comment(driver=driver, post_link=random.choice(post_links), comment=random.choice(comments))
                    time.sleep(random.randrange(config.ACTION_BREAK_MIN_TIME, config.ACTION_BREAK_MAX_TIME))

            account_counter += 1
            # Пауза между разными аккаунтами
            time.sleep(random.randrange(config.ACCOUNT_BREAK_MIN_TIME, config.ACCOUNT_BREAK_MAX_TIME))

        close_driver(driver=driver)


@click.command(name="spam_robot")
@click.option("--links-num", default=1, help="Количество ссылок, обрабатываемых за один сеанс.")
@click.option("--is-follow", is_flag=True, help="Подписываться ли на аккаунты.")
@click.option("--is-message", is_flag=True, help="Отправлять ли сообщение аккаунтам.")
@click.option("--is-comment", is_flag=True, help="Оставлять ли комментарий к первому посту.")
def run(links_num, is_follow, is_message, is_comment):
    """
    Робот, который подписывается, пишет сообщения или комментарии к аккаунтам Instagram.
    """
    main(links_num, is_follow, is_message, is_comment)