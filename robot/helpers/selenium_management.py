import random
import time
import requests

from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List
from selenium.webdriver.remote.webelement import WebElement


def start_driver(attempts: int = 3, options: webdriver.ChromeOptions = None, logs: bool = True) -> webdriver.Chrome:
    if options is None:
        options = webdriver.ChromeOptions()

    for attempt in range(attempts):
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            if logs:
                print(f'Попытка #{attempt}\nОшибка запуска драйвера: {str(e)}.')
            time.sleep(3)
    else:
        raise Exception('Не получилось запустить chromedriver. Версии chrome и chromedriver должны совпадать.')


def open_link(driver: webdriver, link, attempts: int = 3, logs: bool = True) -> bool:
    for attempt in range(attempts):
        try:
            driver.get(link)
            time.sleep(random.randrange(1, 3))
            # FIXME add validator url driver
            return True
        except Exception as e:
            if logs:
                print(f'Попытка #{attempt}\nОшибка открытия ссылки: {str(e)}.')
            time.sleep(5)
    else:
        raise Exception(f'Ссылка "{link}" недоступна или не найдена.')


def get_wait_driver(driver: webdriver, delay: int = 10):
    return WebDriverWait(driver, delay)
    

def check_page_opening(url, driver=None):
    """
    Проверяет, что страница открылась корректно, используя HTTP-запрос для проверки статуса.

    :param url: str, URL страницы.
    :param driver: selenium.webdriver, опционально переданный экземпляр WebDriver.
    :return: bool, True, если страница открыта корректно, иначе False.
    """
    try:
        # Если драйвер не передан, создаём новый
        if driver is None:
            driver = webdriver.Chrome()

        # Открываем страницу с помощью Selenium
        driver.get(url)

        # Дополнительная проверка: проверяем, совпадает ли URL после редиректа
        if driver.current_url != url:
            print(f"Внимание: редирект на {driver.current_url}.")
        else:
            print("URL совпадает, страница открыта корректно.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка HTTP-запроса: {e}")
        return False
    except WebDriverException as e:
        print(f"Ошибка Selenium: {e}")
        return False


def get_wait_element(driver: webdriver, by: By, searched_elem: str, delay: int = 30, attempts: int = 3,
                     sleep: int = 0, is_error: bool = True, logs: bool = False) -> WebElement | str:
    for attempt in range(attempts):
        try:
            time.sleep(sleep)
            wait_driver = get_wait_driver(driver, delay)
            element = wait_driver.until(
                EC.presence_of_element_located((by, searched_elem))
            )
            if element.is_enabled():
                return element
            else:
                print(f'Элемент "searched_elem" недоступен!')
                time.sleep(3)
                continue
        except Exception as e:
            if logs:
                print(f'Попытка #{attempt}\nОшибка получения элемента "{searched_elem}": {str(e)}.')
            time.sleep(5)
    else:
        if is_error:
            raise Exception(f'Элемент "{searched_elem}" не найден.')
        else:
            return ''


def get_wait_elements(driver: webdriver, by: By, searched_elem: str, delay: int = 30, attempts: int = 3,
                      sleep: int = 0, is_error: bool = True, logs: bool = False) -> List[WebElement]:
    for attempt in range(attempts):
        try:
            time.sleep(sleep)
            wait_driver = get_wait_driver(driver, delay)
            return wait_driver.until(
                EC.presence_of_all_elements_located((by, searched_elem))
            )
        except Exception as e:
            if logs:
                print(f'Попытка #{attempt}\nОшибка получения элементов "{searched_elem}": {str(e)}.')
            time.sleep(3)
    else:
        if is_error:
            raise Exception(f'Элементы "{searched_elem}" не найдены.')
        else:
            return []


def close_driver(driver: webdriver, logs: bool = True):
    try:
        driver.close()
        driver.quit()
    except Exception as e:
        if logs:
            print(f'Ошибка при закрытии драйвера: "{e}"')


def get_link_elements(parent_element: webdriver) -> List[WebElement]:
    link_elements = get_wait_elements(
        driver=parent_element,
        by=By.TAG_NAME,
        searched_elem='a',
        delay=10,
        attempts=1,
        is_error=False
    )
    return link_elements


def get_links(link_elements: List[WebElement]) -> list:
    """
    Поиск ссылок в дочерних элементах из родительского элемента
    """

    # Сбор и вывод всех ссылок
    link_list = set()
    for link_element in link_elements:
        href = link_element.get_attribute("href")
        if href:
            link_list.add(href)
    return list(link_list) or []
