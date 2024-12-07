import time
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium_management import start_driver, open_link, get_wait_element, get_wait_elements, close_driver
from utils import get_links


driver = start_driver()

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
    
    time.sleep(10)
    return True

auth(driver=driver, username='odintsovmaxim4@gmail.com', password='password1923DF!')


###############################
### Парсинг ссылок на посты ###
###############################

def get_links(parent_element: webdriver) -> set:
    """
    Поиск ссылок в дочерних элементах из родительского элемента
    """
    # link_elements = parent_element.find_elements(By.TAG_NAME, 'a')
    link_elements = get_wait_elements(driver=parent_element, by=By.TAG_NAME, searched_elem='a')
    
    # Сбор и вывод всех ссылок
    link_list = []
    for link_element in link_elements:
        href = link_element.get_attribute("href")
        if href:
            link_list.append(href)
    return link_list


def get_post_links(driver: webdriver, wait_time: int = 5, max_scrolls: int = 10) -> set:
    """Скроллинг страниц и поиск ссылок"""

    last_height = driver.execute_script("return document.body.scrollHeight")
    post_links = set()
    for i in range(1, max_scrolls+1):
        # Получение ссылок
        if i % 2 == 0:
            posts_parent_elelemt = get_wait_element(driver=driver, by=By.XPATH, searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[2]')
            new_links = get_links(parent_element=posts_parent_elelemt)
            print(f'Найдены новые ссылки на посты: {new_links}')
            post_links.update(new_links)

        # Скролл страницы
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:  # Если конец страницы
            break
        last_height = new_height
    return post_links


# Переход на страницу с постами
search_query = '%23rapmusic' # %23r = #
link = f'https://www.instagram.com/explore/search/keyword/?q={search_query}'
open_link(driver=driver, link=link)


post_links = get_post_links(driver, max_scrolls=6)
post_links = list(post_links)
print(f"Найдено {len(post_links)} ссылок на посты")
# for href in post_links:
#     print(href)
    
    
    

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
            more_accounts_element = get_wait_element(
                driver=driver, 
                by=By.XPATH, 
                searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div/div/div/span/span[2]/a/span',
                delay=5,
                attempts=1,
                is_error=False
            )
            if more_accounts_element and 'ещё' in more_accounts_element.text:
                more_accounts_element.click()
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

