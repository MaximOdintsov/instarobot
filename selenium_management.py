import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List


def start_driver(attempts: int = 3, options: webdriver.ChromeOptions = None) -> webdriver.Chrome:
    if options is None:
        options = webdriver.ChromeOptions()

    for attempt in range(attempts):
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f'Попытка #{attempt}\nОшибка запуска драйвера: {str(e)}.')
            time.sleep(3)
    else:
        raise Exception('Не получилось запустить chromedriver. Версии chrome и chromedriver должны совпадать.')


def open_link(driver: webdriver, link, attempts: int = 3) -> bool:
    for attempt in range(attempts):
        try:
            driver.get(link)
            return True
        except Exception as e:
            print(f'Попытка #{attempt}\nОшибка открытия ссылки: {str(e)}.')
            time.sleep(5)
    else:
        raise Exception(f'Ссылка "{link}" недоступна или не найдена.')


def get_wait_element(driver: webdriver, by: By, searched_elem: str, delay: int = 30, attempts: int = 3,
                     sleep: int = 1, is_error: bool = True) -> webdriver.remote.webelement.WebElement:
    for attempt in range(attempts):
        try:
            time.sleep(sleep)
            element = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((by, searched_elem))
            )
            if element.is_enabled():
                return element
            else:
                print(f'Элемент "searched_elem" недоступен!')
                time.sleep(3)
                continue
        except Exception as e:
            print(f'Попытка #{attempt}\nОшибка получения элемента "{searched_elem}": {str(e)}.')
            time.sleep(5)
    else:
        if is_error:
            raise Exception(f'Элемент "{searched_elem}" не найден.')
        else:
            return False


def get_wait_elements(driver: webdriver, by: By, searched_elem: str, delay: int = 30, attempts: int = 3,
                      sleep: int = 1, is_error: bool = True) -> List[webdriver.remote.webelement.WebElement]:
    for attempt in range(attempts):
        try:
            time.sleep(sleep)
            return WebDriverWait(driver, delay).until(
                EC.presence_of_all_elements_located((by, searched_elem))
            )
        except Exception as e:
            print(f'Попытка #{attempt}\nОшибка получения элементов "{searched_elem}": {str(e)}.')
            time.sleep(3)
    else:
        if is_error:
            raise Exception(f'Элементы "{searched_elem}" не найдены.')
        else:
            return False

def close_driver(driver: webdriver):
    try:
        driver.close()
        driver.quit()
    except Exception as e:
        print(f'Ошибка при закрытии драйвера: {e}')