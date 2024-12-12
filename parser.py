import time
import json
import asyncio
from pathlib import Path
from typing import List
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By

from helpers.selenium_management import start_driver, open_link, get_wait_element, get_wait_elements, close_driver, get_links
from helpers.utils import extract_original_link, parse_activity_data, extract_emails
from helpers.excel import PyXLWriter

from database.orm import async_engine, async_session, insert_account, create_tables, get_all_accounts, get_accounts_not_send, mark_account_as_sent
from database.models import Account

import config


###################
### Авторизация ###
###################
def auth(driver: webdriver, username: str, password: str):
    username = 'odintsovmaxim4@gmail.com'
    password = 'password1923DF!'
    open_link(driver=driver, link="https://www.instagram.com/")
    username_element = get_wait_element(
        driver=driver, 
        by=By.NAME, 
        searched_elem='username',
        delay=5,
    )
    username_element.send_keys(username)

    password_element = get_wait_element(
        driver=driver, 
        by=By.NAME, 
        searched_elem='password',
        delay=5,
    )
    password_element.send_keys(password)

    enter_element = get_wait_element(
        driver=driver, 
        by=By.XPATH, 
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div/div[3]/button/div',
        delay=5,
    )
    enter_element.click()
    time.sleep(5)
    return True


###############################
### Парсинг ссылок на посты ###
###############################
def turn_to_posts_page(driver: webdriver, query: str):
    """
    Переход на страницу с постами
    """
    link = f'https://www.instagram.com/explore/search/keyword/?q={query}'
    open_link(driver=driver, link=link)
    

def get_post_links(driver: webdriver, wait_time: int = 5, max_scrolls: int = 10) -> set:
    """
    Скроллинг страниц и поиск ссылок
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    post_links = set()
    max_scrolls += 1
    for i in range(1, max_scrolls):
        # Скролл страницы
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        
        # Получение ссылок
        if i % 2 == 0 or i == max_scrolls-1:
            posts_parent_elelemt = get_wait_element(driver=driver, by=By.XPATH, searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[2]')
            new_links = get_links(parent_element=posts_parent_elelemt)
            print(f'Найдены новые ссылки на посты: {new_links}')
            post_links.update(new_links)
            
        # Проверка конца страницы
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    return post_links


##################################
### Парсинг ссылок на аккаунты ###
##################################
def accounts_parsing(driver: webdriver, post_link: str) -> list:
    """
    Функция для парсинга аккаунтов из поста
    """
    find_links = False
    open_link(driver=driver, link=post_link)
    
    # Поиск одного аккаунта в посте
    accounts_parent = get_wait_element(
        driver=driver, 
        by=By.XPATH, 
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div[1]/div/div/div/span/span',
        delay=5,
        attempts=1,
        is_error=False
    )
    if accounts_parent:
        print('Найдено в "Поиск одного аккаунта в посте"')
        find_links = True
        
    # Поиск "ещё" в указанных аккаунтах поста
    if find_links is False:
        modal_accounts_element = get_wait_element(
            driver=driver, 
            by=By.XPATH, 
            searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div/div/div/span/span[2]/a/span',
            delay=2,
            attempts=1,
            is_error=False
        )
        if modal_accounts_element and 'ещё' in modal_accounts_element.text:
            modal_accounts_element.click()  # Открытие модального окна с ссылками на аккаунты
            accounts_parent = get_wait_element(
                driver=driver, 
                by=By.XPATH, 
                searched_elem='/html/body/div[6]/div[1]/div/div[2]/div/div/div',
                sleep=1,
                delay=5,
                attempts=1,
                is_error=False
            )
            if accounts_parent:
                print('Найдено в "Поиск "ещё" в указанных аккаунтах поста"')
                find_links = True
    
    # Поиск двух указанных аккаунтов в посте
    if find_links is False:
        accounts_parent = get_wait_element(
            driver=driver, 
            by=By.XPATH, 
            searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div/div/div',
            delay=2,
            attempts=1,
            is_error=False
        )
        if accounts_parent:
            print('Найдено в "Поиск двух указанных аккаунтов в посте"')
            find_links = True
    
    # Поиск ссылок на аккаунты из родительского элемента
    if find_links is True:
        account_link = get_links(accounts_parent)
        print(f'Найдены ссылки: {account_link}')
        return account_link
    

######################################
### Парсинг информации об аккаунте ###
######################################
def parsing_account_info(driver: webdriver, account_link: str) -> dict:
    """
    Парсинг основной информации об аккаунте
    """
    driver.get(account_link)
    time.sleep(3)
    
    links = set()
    description = None
    activity_attrs = {}
    
    #################################
    ### Парсинг описания аккаунта ###
    #################################
    account_description_parent_element = get_wait_element(  # Элемент со всей указанной информацией об аккаунте
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]',
        delay=3,
        attempts=1,
        is_error=False
    )
    desctiption_span_elements = get_wait_elements(  # Элементы span из описания аккаунта\n",
        driver=account_description_parent_element,
        by=By.TAG_NAME,
        searched_elem='span',
        delay=3,
        attempts=1,
        is_error=False
    )
    for desctiption_span_element in desctiption_span_elements:  # Нажимаем на кнопку \"ещё\" (раскраываем описание полностью)\n",
        if 'ещё' == desctiption_span_element.text:
            desctiption_span_element.click()

    if account_description_parent_element:
        # Парсинг описания аккаунта
        description = account_description_parent_element.text
        
        # Парсинг ссылок
        # Из описания аккаунта
        find_links_description = get_links(account_description_parent_element)
        links.update([extract_original_link(find_link_description) for find_link_description in find_links_description])
        # Из указанных контактов
        account_links_button_element = get_wait_element(  # Кнопка для перехода в указанные контакты
            driver=account_description_parent_element,
            by=By.TAG_NAME,
            searched_elem='button',
            delay=3,
            attempts=1,
            is_error=False
        )
        if account_links_button_element:
            account_links_button_element.click()  # Открытие модального окна с указанными ссылками
            link_parent_element = get_wait_element(  # Модальное окно с указанными ссылками
                driver=driver, 
                by=By.XPATH, 
                searched_elem='/html/body/div[6]/div[1]/div/div[2]/div/div/div/div',
                delay=4,
                attempts=1,
                sleep=2,
                is_error=False
            )
            
            find_links_modal = get_links(link_parent_element)
            links.update([extract_original_link(find_link_modal) for find_link_modal in find_links_modal])
    print(f'\n___________________\nСсылка на аккаунт: {account_link}\ndescription: {description}\nСсылки: {links}')

    ###################################
    ### Парсинг активности аккаунта ###
    ###################################
    activity_account_parent_element = get_wait_element(  # Родительский элемент с кол-вом постов, подписчиков и подписок
        driver=driver, 
        by=By.XPATH, 
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[3]',
        delay=3,
        attempts=1,
        is_error=False
    )
    if activity_account_parent_element:
        activity_account_attributes_elements = get_wait_elements(  # Родительский элемент с кол-вом постов, подписчиков и подписок
            driver=activity_account_parent_element, 
            by=By.TAG_NAME, 
            searched_elem='li',
            delay=3,
            attempts=1,
            is_error=False
        )
        if activity_account_attributes_elements:
            activity_list = [activity_account_attributes_element.text for activity_account_attributes_element in activity_account_attributes_elements]
            activity_attrs = parse_activity_data(activity_list)  # 'posts', 'subscribers', 'subscriptions'
            print(f'Найдены атрибуты активности: {activity_attrs}')

    account_info = {'description': description, 'links': list(links)} | activity_attrs
    return account_info


###################################
##### ЗАПИСЬ ДАННЫХ В ТАБЛИЦУ #####
###################################
def write_excel(accounts: List[Account], out_path: str = 'data/instagram_data.xlsx'):
    pyxl = PyXLWriter(colors=2)
    
    # Хедеры
    pyxl[1, 1] = "Ссылка на аккаунт"
    pyxl[1, 2] = "Описание страницы"
    pyxl[1, 3] = "Найденная почта"
    pyxl[1, 4] = "Ссылки из контактов"
    pyxl[1, 5] = "Кол-во постов"
    pyxl[1, 6] = "Кол-во подписчиков"
    pyxl[1, 7] = "Кол-во подписок"
    pyxl[1, 8] = "Хэштег, по которому найден аккаунт"
    pyxl[1, 9] = "Дата сохранения"
    pyxl[1, 10] = "Предсказанный тип аккаунта"
    pyxl[1, 11] = "Комментарий верификатора"
    pyxl[1, 12] = "Тип аккаунта (записывается всегда). Возможные значения: ARTIST, BEATMAKER, LABEL, MARKET, COMMUNITY, OTHER"

    # Данные
    for rid, account in enumerate(accounts):
        r = rid + 2
        pyxl[r, 1] = account.link
        pyxl[r, 2] = account.data.get('description', '')
        pyxl[r, 3] = "\n".join(account.data.get('emails', []))
        pyxl[r, 4] = "\n\n".join(account.data.get('links', []))
        pyxl[r, 5] = account.data.get('posts', '')
        pyxl[r, 6] = account.data.get('subscribers', '')
        pyxl[r, 7] = account.data.get('subscriptions', '')
        pyxl[r, 8] = account.data.get('hashtag', '')
        pyxl[r, 9] = account.create_datetime
        pyxl[r, 10] = account.account_type.value
        pyxl[r, 11] = ''
        pyxl[r, 12] = ''
        
    # Сохраняем файл
    pyxl.save(out_path)


async def run(post_query: str, max_scrolls: int = 2):
    datetime_start = datetime.now()
     
    # Запуск драйвера
    driver = start_driver()
    
    # Авториация
    auth(driver=driver, username=config.USERNAME, password=config.PASSWORD)
    
    # Парсинг ссылок на посты
    turn_to_posts_page(driver=driver, query=post_query)
    post_links = get_post_links(driver, max_scrolls=max_scrolls)
    post_links = list(post_links)
    print(f"Найдено {len(post_links)} ссылок на посты")
    
    # Парсинг ссылок на аккаунты
    for post_link in post_links:
        account_links = accounts_parsing(driver=driver, post_link=post_link)
        for account_link in account_links:
            await insert_account(async_session=async_session, account_link=account_link)

    # # Парсинг страничек
    accounts = await get_accounts_not_send(async_session)
    for idx, account in enumerate(accounts):
        print(f'Парсинг акканута #{idx}...')
        account_data = parsing_account_info(driver=driver, account_link=account.link)
        account_data['hashtag'] = post_query.replace('%23', '#')
        account_data['emails'] = extract_emails(account_data.get('description', ''))
        
        await insert_account(async_session=async_session, account_link=account.link, account_data=account_data)
    print(f'Информация об аккаунтах спарсилась и записалась в БД.')
    close_driver(driver=driver)
    
    # Запись времени обработки
    datetime_end = datetime.now()
    time_path = Path('data/time.txt')
    time_path.write_text(f'\n\nКол-во скроллов страницы: "{max_scrolls}"\nНачало обработки: "{datetime_start}"\nКонец обработки: "{datetime_end}"')
    
    # Запись данных в таблицу
    write_excel(accounts=accounts, out_path='data/instagram_data.xlsx')
    for account in accounts:
        await mark_account_as_sent(async_session, account)
    
    
async def main():
    await create_tables(async_engine=async_engine)
    await run(post_query=config.QUERY, max_scrolls=1)


if __name__ == "__main__":
    asyncio.run(main())