import random
import time
import pickle
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from robot.helpers.selenium_management import open_link, get_wait_element, get_wait_elements, get_link_elements, get_links
from robot.helpers.utils import parse_activity_data


####################
### Авторизация
####################
def simple_auth(driver: webdriver, username: str, password: str):
    open_link(driver=driver, link="https://www.instagram.com/accounts/login/")
    print(f'Данные для входа: username: "{username}", password: "{password}"')

    # Логин
    username_element = get_wait_element(
        driver=driver,
        by=By.NAME,
        searched_elem='username',
        delay=10,
    )
    time.sleep(random.randrange(1, 3))
    username_element.send_keys(username)

    # Пароль
    password_element = get_wait_element(
        driver=driver,
        by=By.NAME,
        searched_elem='password',
        delay=5,
    )
    time.sleep(random.randrange(1, 3))
    password_element.send_keys(password)

    # Войти
    driver.switch_to.active_element.send_keys(Keys.ENTER)

    # Страница "Проверьте свою почту"
    check_your_email_element = get_wait_element(
            driver=driver,
            by=By.XPATH,
            searched_elem="//*[normalize-space(text())='Проверьте свою почту']",
            attempts=1,
            delay=5,
            is_error=False
        )
    if check_your_email_element:
        print(f'Инстраграм запросил код для аккаунта "{username}". Пропускаю...')
        return False

    # Сохранить данные для входа в Instagram?
    save_data_element = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem="//*[contains(., 'Сохранить данные для входа')]",
        delay=10,
        attempts=1,
        is_error=False
    )
    if save_data_element:
        time.sleep(random.randrange(1, 3))
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)

    # Проверка входа
    try:
        get_wait_element(
            driver=driver,
            by=By.XPATH,
            searched_elem="//*[normalize-space(text())='Главная']",
            delay=10,
            attempts=1
        )
        print("Вход выполнен успешно, доступ получен!")
        return True
    except Exception:
        print("Не удалось выполнить вход или страница не загрузилась корректно.")
        return False


def cookies_auth(driver: webdriver, cookie_path: str):
    cookie_path = Path(cookie_path)
    if not cookie_path.exists():
        print(f'Куки по пути "{cookie_path}" не существует!')
        return False
    
    open_link(driver=driver, link="https://www.instagram.com/accounts/login/#")
    
    with open(cookie_path, 'rb') as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.refresh()

    # Сохранить данные для входа в Instagram?
    save_data_element = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem="//*[contains(., 'Сохранить данные для входа')]",
        delay=10,
        attempts=1,
        is_error=False
    )
    if save_data_element:
        time.sleep(1)
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)

    # Проверка входа
    try:
        get_wait_element(
            driver=driver,
            by=By.XPATH,
            searched_elem="//*[normalize-space(text())='Главная']",
            delay=10,
            attempts=1
        )
        print("Вход выполнен успешно, доступ получен!")
        return True
    except Exception:
        print("Не удалось выполнить вход или страница не загрузилась корректно.")
        return False


####################
### Парсинг ссылок на посты
####################
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
        delay=5,
        attempts=1,
        is_error=False
    )
    if nothing_found_element and 'не найдено' in nothing_found_element.text.lower():
        return False
    return True


def get_post_links(driver: webdriver, wait_time: int = 5, max_scrolls: int = 10) -> tuple[list, bool]:
    """
    Скроллинг страниц и поиск ссылок
    """
    page_end = False

    last_height = driver.execute_script("return document.body.scrollHeight")
    # Скролл страницы
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Получение ссылок
    posts_parent_elelemt = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body',
        sleep=wait_time,
        delay=20,
        attempts=1,
    )
    link_elements = get_link_elements(posts_parent_elelemt)
    new_links = get_links(link_elements=link_elements)
    print(f'Найдены новые ссылки на посты: {new_links}')

    # Проверка конца страницы
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        page_end = True

    return new_links, page_end


####################
### Парсинг ссылок на аккаунты из поста
####################
def post_parsing(driver: webdriver, post_link: str) -> list:
    """
    Функция для парсинга аккаунтов из поста
    """
    find_links = False
    open_link(driver=driver, link=post_link)
    time.sleep(random.randrange(2, 4))

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
            print('Открыл модальное окно с соавторами!')
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

    # Поиск одного или двух указанных аккаунтов в посте
    if find_links is False:
        accounts_parent = get_wait_element(
                driver=driver,
                by=By.XPATH,
                searched_elem='/html/body',
                delay=5,
                attempts=1,
                is_error=False
            )
        if accounts_parent:
            print('Найдено в "Поиск одного или двух указанных аккаунтов в посте"')
            find_links = True

    # Поиск ссылок на аккаунты из родительского элемента
    if find_links is True:
        link_elements = get_link_elements(driver)
        account_links = get_links(link_elements=link_elements)
        print(f'Получил {len(account_links)} ссылок из поста: {account_links}')
        return account_links
    else:
        print(f'Ссылка(и) не найдена(ы)')
        return []


####################
### Парсинг информации об аккаунте
####################
def parsing_account_info(driver: webdriver, account_link: str) -> dict:
    """
    Парсинг основной информации об аккаунте
    """
    driver.get(account_link)
    time.sleep(random.randrange(2, 4))

    links_contacts = set()
    links_description = set()
    description = ''
    activity_attrs = {}

    # Парсинг описания аккаунта
    for i in [1, 2]:
        account_description_parent_element = get_wait_element(  # Элемент со всей указанной информацией об аккаунте
            driver=driver,
            by=By.XPATH,
            searched_elem=f'/html/body/div[{i}]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[4]',
            delay=5,
            attempts=1,
            is_error=False
        )
        if account_description_parent_element:
            break

    if account_description_parent_element:
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

        # Парсинг описания аккаунта
        description = account_description_parent_element.text

        # Парсинг ссылок из описания аккаунта
        link_elements = get_link_elements(account_description_parent_element)
        find_links_description = get_links(link_elements=link_elements)
        links_description.update(find_links_description)

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
            for i in [4, 5, 6]:  # Поиск элемента с модальным окном
                link_parent_element = get_wait_element(  # Модальное окно с указанными ссылками
                    driver=driver,
                    by=By.XPATH,
                    searched_elem=f'/html/body/div[{i}]',
                    delay=3,
                    attempts=1,
                    sleep=2,
                    is_error=False
                )
                if link_parent_element:
                    link_elements = get_link_elements(link_parent_element)
                    find_links_modal = get_links(link_elements=link_elements)
                    links_contacts.update(find_links_modal)
                    driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                    break

    # Парсинг активности аккаунта
    for i in [1, 2, 3]:  # Элемент с активностостью аккаунта
        activity_account_parent_element = get_wait_element(
            # Родительский элемент с кол-вом постов, подписчиков и подписок
            driver=driver,
            by=By.XPATH,
            searched_elem=f'/html/body/div[{i}]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[3]',
            delay=2,
            attempts=1,
            is_error=False
        )
        if activity_account_parent_element:
            activity_account_attributes_elements = get_wait_elements(
                # Родительский элемент с кол-вом постов, подписчиков и подписок
                driver=activity_account_parent_element,
                by=By.TAG_NAME,
                searched_elem='li',
                delay=3,
                attempts=1,
                is_error=False
            )
            if activity_account_attributes_elements:
                activity_list = [activity_account_attributes_element.text for activity_account_attributes_element in
                                 activity_account_attributes_elements]
                activity_attrs = parse_activity_data(activity_list)  # 'posts', 'subscribers', 'subscriptions'
                print(f'Найдены атрибуты активности: {activity_attrs}')
            break

    account_info = {
        'description': description,
        'links_contacts': list(links_contacts),
        'links_description': list(links_description),
        'posts': activity_attrs.get('posts', -1),
        'subscribers': activity_attrs.get('subscribers', -1),
        'subscriptions': activity_attrs.get('subscriptions', -1)
    }
    return account_info


def account_get_post_links(driver: webdriver, account_link: str) -> list:
    """
    Парсинг ссылок на посты аккаунта
    """
    open_link(driver, account_link)
    posts_parent_element = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem='/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/div[2]',
        delay=15,
        sleep=3,
        attempts=2
    )
    link_elements = get_link_elements(posts_parent_element)
    post_links = get_links(link_elements=link_elements)
    return post_links


####################
### Взаимодействие с аккаунтами
####################
def account_follow(driver: webdriver, account_link: str) -> bool:
    """
    Подписка на аккаунт
    """
    open_link(driver=driver, link=account_link)
    
    # Кнопка "Подписаться"
    follow_button = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem=".//div[contains(text(), 'Подписаться')]",
        delay=15,
        attempts=2,
        is_error=False
    )
    # Нажать "Подписаться"
    if follow_button:
        follow_button.click()
        time.sleep(random.randrange(1, 3))
    
    # Проверка подписки
    check_follow_button = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem=".//div[contains(text(), 'Подписки')]",
        delay=5,
        attempts=1,
        is_error=False,
        logs=False
    )
    if check_follow_button:
        print(f'Подписка на аккаунт оформлена!')
        return True
    else:
        print('Не удалось оформить подписку на аккаунт')
        return False


def account_send_message(driver: webdriver, account_link: str, message: str) -> bool:
    """
    Отправка сообщения аккаунту
    """
    open_link(driver=driver, link=account_link)
    
    # Кнопка "Отправить сообщение"
    send_message_button = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem=".//div[@role='button' and contains(text(), 'Отправить сообщение')]",
        delay=15,
        sleep=3,
        attempts=2,
        is_error=False
    )
    # Нажать "Отправить сообщение"
    if send_message_button:
        send_message_button.click()
        notification_button = get_wait_element(  # Модальное окно "Включить уведомления?"
            driver=driver,
            by=By.XPATH,
            searched_elem="//button[text()='Не сейчас']",
            delay=4,
            sleep=2,
            attempts=1,
            is_error=False
        )
        if notification_button:
            notification_button.click()
            print(f'Перешел в директ аккаунта: {account_link}')
    # Отправить сообщение
    if send_message_button:
        send_message_field_element = get_wait_element(
            driver=driver,
            by=By.XPATH,
            searched_elem=".//div[@role='textbox' and @aria-describedby='Сообщение' and @aria-placeholder='Напишите сообщение…']",
            delay=15,
            sleep=2,
            attempts=1,
            is_error=False
        )
        if send_message_field_element:
            send_message_field_element.clear()
            ActionChains(driver).move_to_element(send_message_field_element).click().send_keys(message).perform()
            time.sleep(random.randrange(2, 5))
            send_message_field_element.send_keys(Keys.ENTER)  # Отправляет коммент
            print(f'Отправил сообщение аккаунту {account_link}')
            return True
    print(f'Не удалось отправить сообщение аккаунту {account_link}')
    return False


def account_send_comment(driver: webdriver, post_link: str, comment: str) -> bool:
    """
    Отправка комментария к посту
    """
    open_link(driver, post_link)
    
    comment_element = get_wait_element(
        driver=driver,
        by=By.XPATH,
        searched_elem='//textarea[@aria-label="Добавьте комментарий..."]',
        delay=15,
        sleep=3,
        attempts=2
    )
    if comment_element:    
        ActionChains(driver).click(comment_element).send_keys(str(comment)).perform()
        time.sleep(random.randrange(2, 5))
        driver.switch_to.active_element.send_keys(Keys.ENTER)  # Отправляет коммент
        print(f'Написал комментарий к посту: {post_link}')
        return True
    print(f'Не получилось написать комментарий к посту: {post_link}')
    return False
