import asyncio
import click
import aiohttp
import gspread
import numpy as np

from robot.helpers.async_utils import url_shortening_async
from robot.helpers.logs import capture_output_to_file
from robot.database.models import Account, AccountType, STATUS
from robot.database.orm import async_session, create_or_update_object, get_object_by_filter, get_objects_by_where
from robot.conf import settings


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
            with open(settings.UPDATE_ERROR_LOGS_PATH, 'a') as f:
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

    # Создание нового аккаунта
    if not account:  # FIXME парсить и остальные данные из таблицы
        data = {'verified_account_type': verified_account_type.value,
                'account_link': account_link}
        account = await create_or_update_object(
            async_session_factory=async_session,
            model=Account,
            filters={'link': account_link},
            defaults={
                'link': account_link,
                'data': data,
                'account_type': verified_account_type,
                'status': STATUS.VALIDATED
            }
        )
        print(f'\nСоздал новый аккаунт в БД из таблицы: "{account.link}"!')
        return True

    # Обновление данных в БД
    if not account.data.get('verified_account_type', ''):
        print(f'\n\n--------\nОбновляю данные в БД для аккаунта "{account.link}"...'
              f'\nТекущий тип аккаунта: "{account.account_type.value}".\nТекущий статус: "{account.status.value}"')
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
        print(f'\nУспешно обновил данные для аккаунта "{account.link}"!'
              f'\nНовый тип аккаунта: "{verified_account_type.value}".\nНовый статус: "{STATUS.VALIDATED.value}".')
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
        account.link,
        account.data.get('description', ''),
        account.data.get('predicted_account_type', AccountType.UNKNOWN.value),
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
    print(row)
    return row


async def get_data_for_table(accounts) -> list:
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


################################
### Получение данных для применения стилей Google Sheets
################################
def get_style_requests(values: list, worksheet_id: int) -> list:
    max_columns = max(len(row) for row in values)

    # Определяем два цвета (цветы указываем в диапазоне от 0 до 1)
    # Цвет #FFFFDD
    color1 = {
        "red": 1.0,
        "green": 1.0,
        "blue": 221/255.0
    }
    # Цвет #DDFFFF
    color2 = {
        "red": 221/255.0,
        "green": 1.0,
        "blue": 1.0
    }

    # Если требуется раскрашивать каждую заполненную строку, то:
    start_row = 2           # если нужно перекрасить первую строку – start_row=1
    end_row = len(values)  # количество заполненных строк

    # Формируем список запросов для batch_update
    requests = []
    for i in range(start_row, end_row + 1):
        # Чередуем цвета: если i - start_row четное – используем первый цвет, иначе второй
        bg_color = color1 if (i - start_row) % 2 == 0 else color2

        # Для каждого ряда формируем запрос, который задаёт форматирование в диапазоне от первого до max_columns столбца.
        # Примечание: индексы строк и столбцов в GridRange начинаются с 0, поэтому строке i соответствует диапазон [i-1, i)
        req = {
            "repeatCell": {
                "range": {
                    "sheetId": worksheet_id,
                    "startRowIndex": i - 1,
                    "endRowIndex": i,
                    "startColumnIndex": 0,
                    "endColumnIndex": max_columns
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": bg_color
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }
        requests.append(req)
        
    return requests



################################
### Запуск основной функции
################################
async def main():
    # Получение данных из таблицы и обновление в БД
    gc = gspread.service_account(filename=settings.GOOGLE_API_TOKEN_PATH)
    worksheet = gc.open(settings.GOOGLE_TABLE_NAME).worksheet(settings.GOOGLE_WORKSHEET_NAME)
    list_of_dicts = worksheet.get_all_records()
    
    updated_count = 0
    for idx, row in enumerate(list_of_dicts):
        idx += 1
        updated = await update_account_from_table(idx, row)
        if updated:
            updated_count += 1
    print(f'{updated_count} аккаунтов обновлено из таблицы {settings.GOOGLE_TABLE_NAME}!')

    # Запись данных из БД в таблицу
    accounts = await get_objects_by_where(
        async_session,
        Account,
        Account.status.in_([STATUS.PARSING])
    )
    data_rows = await get_data_for_table(accounts)
    numpy_array = np.array(data_rows, dtype=object)
    print(f'numpy_array: {numpy_array}')
    worksheet.append_rows(numpy_array.tolist(), value_input_option='USER_ENTERED')  # Добавление новых строк
    print(f'Данные успешно загружены в таблицу {settings.GOOGLE_TABLE_NAME}')

    # Применение стилей к таблице
    values = worksheet.get_all_values()
    style_requests = get_style_requests(values=values, worksheet_id=worksheet.id)
    worksheet.spreadsheet.batch_update(body={"requests": style_requests})
    print(f'Стили успешно применены к таблице {settings.GOOGLE_TABLE_NAME}')

    # Меняем статус на "Отправлено на верификацию"
    for account in accounts:
        await create_or_update_object(
            async_session_factory=async_session,
            model=Account,
            filters={'id': account.id},
            defaults={'status': STATUS.SENT}
        )


@click.command(name="google_table")
@capture_output_to_file("google_table")
def run():
    asyncio.run(main())
