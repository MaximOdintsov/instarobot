import time
import json
import asyncio
import click
import aiohttp
import gspread
import numpy as np

from robot.helpers.async_utils import url_shortening_async
from robot.helpers.logs import capture_output_to_file
from robot.database.models import Account, AccountType, STATUS
from robot.database.orm import  async_session, create_or_update_object, get_object_by_filter, get_objects_by_where
from robot.conf import config


################################
### Обновление данных в БД на верифицированные из таблицы
################################
async def update_account_from_table(idx: int, row: dict):
    # Валидация и обработка данных аккаунта из таблицы
    account_link = row['Ссылка на аккаунт']
    if account_link:
        account_link = account_link.strip()
    else:
        return False
    
    verified_account_type = row['Верифицированный тип аккаунта']
    if verified_account_type:
        try:
            verified_account_type = AccountType(verified_account_type.upper().strip())
            # verified_account_type = verified_account_type
        except ValueError:
            log = f'Ошибка: Неправильное название типа аккаунта: "{verified_account_type}"\nИндекс строки: {idx}.\nДанные: {row}'
            with open(config.UPDATE_ERROR_LOGS_PATH, 'a') as f:
                f.write(log)
            print(log)
            return False
    else:
        return False
    
    # Получение данных об аккаунте из БД
    account = await get_object_by_filter(
        async_session_factory=async_session,
        model=Account,
        filters={'link': account_link}
    )
    
    # Обновление данных в БД
    if not account.data.get('verified_account_type', ''):
        print(f'\n\n--------\nОбновляю данные в БД для аккаунта "{account.link}"...\nТекущий тип аккаунта: "{account.account_type.value}".\nТекущий статус: "{account.status.value}"')
        new_data = account.data
        new_data['verified_account_type'] = verified_account_type.value
        
        await create_or_update_object(
            async_session_factory=async_session,
            model=Account,
            filters={'link': account_link},
            defaults={
                'data': new_data,
                'account_type': verified_account_type,
                'status': STATUS.VALIDATED
            }
        )
        print(f'\nУспешно обновил данные для аккаунта "{account.link}"!\nНовый тип аккаунта: "{verified_account_type.value}".\nНовый статус: "{STATUS.VALIDATED.value}".')
        return True
    return False
    
    
################################
### Получение данных для обновления таблицы Google Sheets
################################
async def async_url_shortening_for_list(urls: list[str], session: aiohttp.ClientSession) -> list[str]:
    """
    Асинхронно сокращает список URL'ов.
    """
    tasks = [url_shortening_async(url, session) for url in urls]
    return await asyncio.gather(*tasks)


async def process_single_account(account, session) -> list:
    """
    Асинхронно обрабатывает один аккаунт:
    - сокращает ссылки,
    - формирует строку данных для массива.
    """

    emails = account.data.get('emails', [])
    links_description_list = account.data.get('links_description', [])
    links_contacts_list = account.data.get('links_contacts', [])

    shortened_links_description = (
        await async_url_shortening_for_list(links_description_list, session)
        if links_description_list else []
    )
    shortened_links_contacts = (
        await async_url_shortening_for_list(links_contacts_list, session)
        if links_contacts_list else []
    )

    row = [
        account.data.get('account_link', ''),
        account.data.get('description', ''),
        account.data.get('predicted_account_type', AccountType.UNKNOWN),
        account.data.get('verified_account_type', ''),
        "\n".join(emails),
        "\n".join(shortened_links_description),
        "\n".join(shortened_links_contacts),
        account.data.get('posts', ''),
        account.data.get('subscribers', ''),
        account.data.get('subscriptions', ''),
        account.data.get('hashtag', ''),
        str(account.create_datetime),
    ]
    return row


async def get_data_for_table(accounts) -> np.ndarray:
    """
    Формирует данные для отправки в таблицу
    """
    async with aiohttp.ClientSession() as session:
        # Формируем задачи для параллельной обработки каждого аккаунта
        tasks = [
            process_single_account(account, session)
            for account in accounts
        ]
        data_rows = await asyncio.gather(*tasks)
        return data_rows


async def main():
    # Получение данных из таблицы и обновление в БД
    gc = gspread.service_account(filename=config.GOOGLE_API_TOKEN_PATH)
    worksheet = gc.open(config.GOOGLE_TABLE_NAME).worksheet(config.GOOGLE_WORKSHEET_NAME)
    list_of_dicts = worksheet.get_all_records()
    for idx, row in enumerate(list_of_dicts):
        idx += 1
        await update_account_from_table(idx, row)
    print(f'Данные выгружены из таблицы {config.GOOGLE_TABLE_NAME} и записаны в БД')
    
    
    # Запись данных в таблицу
    accounts = await get_objects_by_where(
        async_session,
        Account,
        Account.status.in_([STATUS.READY, STATUS.SENT, STATUS.VALIDATED])
    )
    data_rows = await get_data_for_table(accounts)
    numpy_array = np.array(data_rows, dtype=object)
    worksheet.update(numpy_array.tolist(), 'A2')  # Заполнение начинается с ячейки A2
    print(f'Данные успешно загружены в таблицу {config.GOOGLE_TABLE_NAME}')


    # Меняем статус на "Отправлено на верификацию"
    accounts = await get_objects_by_where(
        async_session,
        Account,
        Account.status.in_([STATUS.READY])
    )
    for account in accounts:
        await create_or_update_object(
            async_session_factory=async_session,
            model=Account,
            filters={'id': account.id},
            defaults={'status': STATUS.SENT}
        )


@click.command(name="update_google_table")
@capture_output_to_file("update_google_table")
def run():
    asyncio.run(main())
