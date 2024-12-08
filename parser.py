import time
import json
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium_management import start_driver, open_link, get_wait_element, get_wait_elements, close_driver, get_links
from utils import extract_original_link
from excel import PyXLWriter


driver = start_driver()
MAX_SCROLLS = 10


###################
### Авторизация ###
###################
def auth(driver: webdriver, username: str, password: str):
    username = 'odintsovmaxim4@gmail.com'
    password = 'password1923DF!'
    open_link(driver=driver, link="https://www.instagram.com/")
    username_element = get_wait_element(driver=driver, by=By.NAME, searched_elem='username')
    username_element.send_keys(username)

    password_element = get_wait_element(driver=driver, by=By.NAME, searched_elem='password')
    password_element.send_keys(password)

    enter_element = get_wait_element(driver=driver, by=By.XPATH, searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div/div[3]/button/div')
    enter_element.click()
    time.sleep(5)
    return True

auth(driver=driver, username='odintsovmaxim4@gmail.com', password='password1923DF!')


###############################
### Парсинг ссылок на посты ###
###############################
def turn_to_posts_page(driver: webdriver, query: str):
    """Переход на страницу с постами"""
    link = f'https://www.instagram.com/explore/search/keyword/?q={query}'
    open_link(driver=driver, link=link)
    

def get_post_links(driver: webdriver, wait_time: int = 5, max_scrolls: int = 10) -> set:
    """Скроллинг страниц и поиск ссылок"""

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


# Переход на страницу с постами
turn_to_posts_page(driver=driver, query='%23rapmusic') # '%23r' == '#'
post_links = get_post_links(driver, max_scrolls=MAX_SCROLLS)
post_links = list(post_links)
print(f"Найдено {len(post_links)} ссылок на посты")


##################################
### Парсинг ссылок на аккаунты ###
##################################

def accounts_parsing(post_links: List[str]) -> set:
    account_links = set()
    for post_link in post_links:
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
                delay=5,
                attempts=1,
                is_error=False
            )
            if modal_accounts_element and 'ещё' in modal_accounts_element.text:
                modal_accounts_element.click()  # Открытие модального окна с ссылками на аккаунты
                accounts_parent = get_wait_element(
                    driver=driver, 
                    by=By.XPATH, 
                    searched_elem='/html/body/div[6]/div[1]/div/div[2]/div/div/div',
                    sleep=3,
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
                delay=5,
                attempts=1,
                is_error=False
            )
            if accounts_parent:
                print('Найдено в "Поиск двух указанных аккаунтов в посте"')
                find_links = True
        
        # Поиск ссылок на аккаунты из родительского элемента
        if find_links is True:
            new_links = get_links(accounts_parent)
            print(f'Найдены ссылки: {new_links}')
            account_links.update(new_links)
            
    return account_links


account_links = accounts_parsing(post_links)
account_links = list(account_links)
print(f"Найдено {len(account_links)} ссылок на аккаунты")



################################################
### Парсинг информации о найденных аккаунтах ###
################################################


def parsing_account_info(driver: webdriver, account_link: str) -> dict:
    """
    Парсинг основной информации об аккаунте
    """
    driver.get(account_link)
    time.sleep(3)
    
    links = None
    all_description = None
    
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

        # Парсинг ссылок, указанных в контактах аккаунта
        account_links_button_element = get_wait_element(  # Кнопка с указанными ссылками
            driver=account_description_parent_element,
            by=By.TAG_NAME,
            searched_elem='button',
            delay=3,
            attempts=1,
            is_error=False
        )
        if account_links_button_element and '+' in account_links_button_element.text:  # Если указано несколько ссылок 
            account_links_button_element.click()  # Открытие модального окна с указанными ссылками
            link_parent_element = get_wait_element(  # Модальное окно с указанными ссылками
                driver=account_links_button_element, 
                by=By.XPATH, 
                searched_elem='/html/body/div[6]/div[1]/div/div[2]/div/div/div/div',
                delay=4,
                attempts=1,
                sleep=2,
                is_error=False
            )
            
            find_links = get_links(link_parent_element)
            links = [extract_original_link(find_link) for find_link in find_links]
        if not links:  # Если в указанных ссылках нет "+ n"
            find_links = get_links(account_description_parent_element)
            links = [extract_original_link(find_link) for find_link in find_links]
        
    print(f'\n___________________\nСсылка на аккаунт: {account_link}\nall_description: {all_description}\nСсылки: {links}')
    account_info = {'account_link': account_link, 'all_description': all_description, 'links': links}
    return account_info


accounts = []
for account_link in account_links:
    accounts_info = parsing_account_info(driver=driver, account_link=account_link)
    accounts.append(accounts_info)
close_driver(driver=driver)


#########################
##### ЗАПИСЬ ДАННЫХ #####
#########################

#####################
### В json формат ###
#####################
with open('data.json', 'w') as f:
    data = json.dump(accounts, indent=4, ensure_ascii=False, fp=f)
    
#################
### В таблицу ###
#################
pyxl = PyXLWriter(colors=2)
# Хедеры
pyxl[1, 1] = "Ссылка на аккаунт"
pyxl[1, 2] = "Описание страницы"
pyxl[1, 3] = "Ссылки из контактов"
# Данные
for rid, account_item in enumerate(accounts):
    r = rid + 2
    pyxl[r, 1] = account_item.get('account_link')
    pyxl[r, 2] = account_item.get('all_description')
    pyxl[r, 3] = "\n------------------------------\n".join(account_item.get('links'))

# Сохраняем файл
pyxl.save("instagram_data.xlsx")

    
