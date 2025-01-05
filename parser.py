import json
import joblib
import asyncio
import pandas as pd

from selenium import webdriver

from helpers.selenium_management import start_driver, close_driver
from helpers.utils import extract_emails
from helpers.utils import POST_VALUE, ACCOUNT_VALUE, validate_instagram_url
from database.orm import async_engine, async_session, insert_account, create_tables, get_accounts_not_processed, get_accounts_not_send, mark_account_as_sent
from helpers.excel import write_excel
import config
from robot import auth, turn_to_posts_page,get_post_links, accounts_parsing, parsing_account_info


async def parsing(driver: webdriver, post_query: str, max_scrolls: int = 2):
    # Загрузка модели
    account_type_model = joblib.load(config.ACCOUNT_TYPE_MODEL_PATH)

    accounts = await get_accounts_not_processed(async_session)
    if not accounts:
        # Проверка, найдены ли посты по хэштегу
        posts_found = turn_to_posts_page(driver=driver, query=post_query)
        if not posts_found:
            return

        # Парсинг ссылок на посты
        post_links = get_post_links(driver, max_scrolls=max_scrolls)
        post_links = list(post_links)
        for post_link in post_links:
            link_type = validate_instagram_url(post_link)
            if link_type != POST_VALUE:
                post_links.remove(post_link)
        print(f"Найдено {len(post_links)} ссылок на посты")

        # Парсинг постов (берет ссылки на аккаунты)
        for idx, post_link in enumerate(post_links):
            print(f'Парсинг поста #{idx}. Ссылка: {post_link}')
            account_links = accounts_parsing(driver=driver, post_link=post_link)
            for account_link in account_links:
                link_type = validate_instagram_url(account_link)
                if link_type == ACCOUNT_VALUE:
                    await insert_account(async_session=async_session, account_link=account_link)

    # Парсинг страничек
    accounts = await get_accounts_not_processed(async_session)
    accounts_len = len(accounts)
    for idx, account in enumerate(accounts):
        print(f'Парсинг акканута #{idx}. Ссылка: {account.link}. Всего аккаунтов для обработки: {accounts_len}')

        # Запись данных об аккаунте
        account_data = parsing_account_info(driver=driver, account_link=account.link)
        account_data['account_link'] = account.link
        account_data['hashtag'] = post_query.replace('%23', '#')
        account_data['emails'] = extract_emails(account_data.get('description', ''))

        print('Описание страницы', account_data.get('description', ''))
        print('Ссылки из описания', "\n".join(account_data.get('links_description', [])))
        print('Ссылки из контактов', "\n".join(account_data.get('links_contacts', [])))
        print('Почта существует', 1 if account_data.get('emails', '') else 0)
        print('Кол-во постов', account_data.get('posts', ''))

        # Предсказание типа аккаунта
        df = pd.DataFrame(
            {
                'Описание страницы': [account_data.get('description', '')],
                'Ссылки из описания': ["\n".join(account_data.get('links_description', []))],
                'Ссылки из контактов': ["\n".join(account_data.get('links_contacts', []))],
                'Почта существует': [1 if account_data.get('emails', '') else 0],  # приводим в строковое значение
                'Кол-во постов': [account_data.get('posts', '')]
            }
        )

        preds = account_type_model.predict(df)
        account_data['predicted_account_type'] = preds[0]

        # Сохранение данных аккаунта
        await insert_account(
            async_session=async_session,
            account_link=account.link,
            account_type=account_data['predicted_account_type'],
            is_processed=True,
            account_data=account_data,
        )
    print(f'Информация об аккаунтах спарсилась и записалась в БД.')


async def main():
    await create_tables(async_engine=async_engine)

    # Проверка
    with open(config.AUTH_DATA_PATH, "r", encoding="utf-8") as file:
        auth_data_list = json.load(file)
    auth_data = auth_data_list[1]
    username = auth_data.get('username')
    password = auth_data.get('password')
    if not username or not password:
        raise Exception(f'В первом элементе нет username: "{username}" или password: "{password}"')

    # Запуск драйвера
    driver = start_driver()

    # Авториация
    auth(driver=driver, username=username, password=password)

    # Парсинг запросов
    with open(config.QUERIES_PATH, "r", encoding="utf-8") as file:
        queries = json.load(file)
    
    # Запуск парсера
    for query in queries:
        await parsing(driver=driver, post_query=f'%23{query}', max_scrolls=1)  # '%23' == '#'
    close_driver(driver=driver)

    # Запись данных в таблицу
    accounts = await get_accounts_not_send(async_session)
    write_excel(accounts=accounts, out_path=config.INSTA_ACCOUNTS_DATA_PATH)
    for account in accounts:
        await mark_account_as_sent(async_session, account)


if __name__ == "__main__":
    asyncio.run(main())