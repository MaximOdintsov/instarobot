import time
import json
from typing import List
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By

from helpers.selenium_management import start_driver, open_link, get_wait_element, get_wait_elements, close_driver, get_links
from helpers.utils import extract_original_link, parse_activity_data
from helpers.excel import PyXLWriter
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
    

################################################
### Парсинг информации о найденных аккаунтах ###
################################################
def parsing_account_info(driver: webdriver, account_link: str) -> dict:
    """
    Парсинг основной информации об аккаунте
    """
    driver.get(account_link)
    time.sleep(3)
    
    links = set()
    all_description = None
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
    if account_description_parent_element:
        # Парсинг описания аккаунта
        all_description = account_description_parent_element.text
        
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
    print(f'\n___________________\nСсылка на аккаунт: {account_link}\nall_description: {all_description}\nСсылки: {links}')

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
            activity_attrs = parse_activity_data(activity_list)
            print(f'Найдены атрибуты активности: {activity_attrs}')

    account_info = {'account_link': account_link, 'all_description': all_description, 'links': list(links)} | activity_attrs
    return account_info


#########################
##### ЗАПИСЬ ДАННЫХ #####
#########################
# # Запись в json
# with open('data/data.json', 'w') as f:
#     data = json.dump(accounts_info_list, indent=4, ensure_ascii=False, fp=f)
    
# # Запись в таблицу
# pyxl = PyXLWriter(colors=2)
# # Хедеры
# pyxl[1, 1] = "Ссылка на аккаунт"
# pyxl[1, 2] = "Описание страницы"
# pyxl[1, 3] = "Ссылки из контактов"
# pyxl[1, 4] = "Кол-во постов"
# pyxl[1, 5] = "Кол-во подписчиков"
# pyxl[1, 6] = "Кол-во подписок"
# # Запись данных в таблицу
# for rid, account_item in enumerate(accounts_info_list):
#     r = rid + 2
#     pyxl[r, 1] = account_item.get('account_link')
#     pyxl[r, 2] = account_item.get('all_description')
#     pyxl[r, 3] = "\n------------------------------\n".join(account_item.get('links'))
#     pyxl[r, 4] = str(account_item.get('posts'))
#     pyxl[r, 5] = str(account_item.get('subscribers'))
#     pyxl[r, 6] = str(account_item.get('subscriptions'))
# # Сохраняем файл
# pyxl.save("data/instagram_data.xlsx")

    
from database.orm import insert_new_account, async_session
import asyncio

async def run(post_query: str, max_scrolls: int = 2):
    with open('data/time.txt', 'a') as f:
        f.write(f'\n\nКол-во скроллов страницы для поиска постов: "{max_scrolls}"\nНачало обработки: "{datetime.now()}"')
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
    account_links = set()
    for post_link in post_links:
        account_link = accounts_parsing(driver=driver, post_link=post_link)
        account_links.update(account_link)
    account_links = list(account_links)
    print(f"Найдено {len(account_links)} ссылок на аккаунты")
    
    # Парсинг страничек
    for idx, account_link in enumerate(account_links):
        print(f'Парсинг акканута #{idx}...')
        account_info = parsing_account_info(driver=driver, account_link=account_link)
        account_info['hashtag'] = post_query.replace('%23r', '#')
        insert_new_account(async_session=async_session, data=account_info)
    print(f'Информация об аккаунтах спарсилась и записалась в БД.')
    
    close_driver(driver=driver)
    with open('data/time.txt', 'a') as f:
        f.write(f'\nКонец обработки: "{datetime.now()}"')
    
    
asyncio.run(run(post_query='%23upcomingrapper', max_scrolls=1))  # '%23r' == '#'
