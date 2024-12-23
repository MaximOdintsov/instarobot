import random
import time


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


from helpers.selenium_management import open_link, get_wait_element, get_wait_elements, get_links
from helpers.utils import extract_original_link, parse_activity_data




###################
### Авторизация ###
###################
def auth(driver: webdriver, username: str, password: str):
    open_link(driver=driver, link="https://www.instagram.com/")
    time.sleep(random.randrange(1, 3))
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
    time.sleep(random.randrange(3, 5))
    
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
    nothing_found_element = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div/div[2]/span',
        delay=3,
        is_error=False
    )
    if nothing_found_element and 'не найдено' in nothing_found_element.text.lower():
        return False
    return True


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
def accounts_parsing(driver: webdriver, post_link: str) -> set:
    """
    Функция для парсинга аккаунтов из поста
    """
    find_links = False
    open_link(driver=driver, link=post_link)
    time.sleep(random.randrange(2, 4))

    # Поиск одного аккаунта в посте
    accounts_parent = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div[1]',
        delay=3,
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
            modal_accounts_element.click()  # Открытие модального окна со ссылками на аккаунты
            accounts_parent = get_wait_element(
                driver=driver,
                by=By.XPATH,
                searched_elem='/html/body/div[6]/div[1]/div/div[2]/div/div/div',
                sleep=2,
                delay=3,
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
            delay=random.randrange(2, 3),
            attempts=1,
            is_error=False
        )
        if accounts_parent:
            print('Найдено в "Поиск двух указанных аккаунтов в посте"')
            find_links = True

    # Поиск ссылок на аккаунты из родительского элемента
    if find_links is True:
        account_links = get_links(accounts_parent)
        print(f'Найдены ссылки: {account_links}')
        return account_links
    return []


######################################
### Парсинг информации об аккаунте ###
######################################
def parsing_account_info(driver: webdriver, account_link: str) -> dict:
    """
    Парсинг основной информации об аккаунте
    """
    driver.get(account_link)
    time.sleep(random.randrange(2, 4))

    links_contacts = set()
    links_description = set()
    description = None
    activity_attrs = {}

    # Парсинг описания аккаунта
    account_description_parent_element = get_wait_element(  # Элемент со всей указанной информацией об аккаунте
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]',
        delay=5,
        attempts=1,
        is_error=False
    )
    desctiption_span_elements = get_wait_elements(  # Элементы span из описания аккаунта\n",
        driver=account_description_parent_element,
        by=By.TAG_NAME,
        searched_elem='span',
        delay=2,
        attempts=1,
        is_error=False
    )
    for desctiption_span_element in desctiption_span_elements:  # Нажимаем на кнопку "ещё" (раскрываем описание)
        if 'ещё' == desctiption_span_element.text:
            desctiption_span_element.click()
            time.sleep(random.randrange(1, 2))

    if account_description_parent_element:
        # Парсинг описания аккаунта
        description = account_description_parent_element.text

        # Парсинг ссылок из описания аккаунта
        find_links_description = get_links(account_description_parent_element)
        links_description.update([extract_original_link(find_link_description) for find_link_description in find_links_description])

        # Парсинг ссылок из окна контактов
        account_links_button_element = get_wait_element(  # Кнопка для перехода в указанные контакты
            driver=account_description_parent_element,
            by=By.TAG_NAME,
            searched_elem='button',
            delay=2,
            attempts=1,
            is_error=False
        )
        if account_links_button_element:
            account_links_button_element.click()  # Открытие модального окна с указанными ссылками
            for i in [5, 6]:  # Поиск элемента с модальным окном
                link_parent_element = get_wait_element(  # Модальное окно с указанными ссылками
                    driver=driver,
                    by=By.XPATH,
                    searched_elem=f'/html/body/div[{i}]/div[1]/div/div[2]/div/div/div',
                    delay=3,
                    attempts=1,
                    sleep=2,
                    is_error=False
                )
                if link_parent_element:
                    find_links_modal = get_links(link_parent_element)
                    links_contacts.update([extract_original_link(find_link_modal) for find_link_modal in find_links_modal])
                    break
    print(f'\n___________________\nСсылка на аккаунт: {account_link}\ndescription: {description}\n'
          f'Ссылки из описания: {links_description}\nСсылки из контактов: {links_contacts}')

    # Парсинг активности аккаунта
    activity_account_parent_element = get_wait_element(  # Родительский элемент с кол-вом постов, подписчиков и подписок
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[3]',
        delay=2,
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
    account_info = {'description': description,
                    'links_contacts': list(links_contacts),
                    'links_description': list(links_description)} | activity_attrs
    return account_info


#########################################################
### Подписка и отправка рандомного сообщения аккаунту ###
#########################################################
def send_message_and_follow(driver: webdriver, account_link: str, message: str):
    open_link(driver=driver, link=account_link)
    time.sleep(2)

    # Подписка + сообщение
    follow_button = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem=".//div[contains(text(), 'Подписаться')]",
        delay=2,
        attempts=2,
        is_error=False
    )
    send_message_button = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem=".//div[@role='button' and contains(text(), 'Отправить сообщение')]",
        delay=2,
        attempts=2,
        is_error=False
    )

    # Нажать "Подписаться"
    if follow_button:
        follow_button.click()
        time.sleep(random.randrange(1, 3))
        print(f'Подписался на аккаунт')

    # Нажать "Отправить сообщение"
    if send_message_button:
        send_message_button.click()
        notification_button = get_wait_element(  # Модальное окно "Включить уведомления?"
            driver=driver,
            by=By.XPATH,
            searched_elem="//button[text()='Не сейчас']",
            delay=3,
            logs=False,
            is_error=False,
            attempts=1
        )
        if notification_button:
            notification_button.click()
            print(f'Перешел в директ')

    # Отправить рандомный шаблон сообщения
    if send_message_button:
        send_message_field_element = get_wait_element(
            driver=driver,
            by=By.XPATH,
            searched_elem=".//div[@role='textbox' and @aria-describedby='Сообщение' and @aria-placeholder='Напишите сообщение…']",
            delay=2,
            attempts=2,
            is_error=False
        )
        if send_message_field_element:
            send_message_field_element.clear()
            ActionChains(driver).move_to_element(send_message_field_element).click().send_keys(message).perform()
            time.sleep(random.randrange(1, 4))
            send_message_field_element.send_keys(Keys.ENTER)
            time.sleep(random.randrange(2, 4))
            print(f'Отправил сообщение')