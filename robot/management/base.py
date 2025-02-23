from typing import List, Dict

from robot.helpers.selenium_management import start_driver, close_driver
from robot.robot import cookies_auth
from robot.conf import settings


class MultiInstagramAccountDriver:
    """
    Класс, который создает driver и автоматически авторизуется в instagram.
    Зависит от функции robot.robot.auth
    """
    def __init__(self, accounts: List[str]):
        """
        accounts: список с именами аккаунтов (имя из data/instagram_cookies/ без .pkl),
        """
        self.accounts = accounts
        self.current_index = 0
        self.driver = None

    def start_new_driver(self):
        """Создаёт новый экземпляр драйвера."""
        self.driver = start_driver()

    def close_current_driver(self):
        """Закрывает текущий драйвер, если он запущен."""
        if self.driver:
            close_driver(self.driver)
            self.driver = None

    def get_current_account(self):
        """Возвращает данные текущего аккаунта или None, если они закончились."""
        if self.current_index < len(self.accounts):
            return self.accounts[self.current_index]
        return None

    def switch_account(self):
        """
        Меняет аккаунт и авторизуется
        """
        self.current_index += 1
        self.authenticate()

    def authenticate(self):
        """
        Закрывает старый драйвер.
        Пытается авторизоваться с текущим аккаунтом.
        Если авторизация не удалась или произошла ошибка, автоматически переключается на следующий аккаунт.
        Возвращает драйвер с авторизованным аккаунтом.
        """
        account = self.get_current_account()  # username
        if not account:
            raise Exception("Нет аккаунтов для авторизации.")

        while account:
            self.close_current_driver()
            self.start_new_driver()
            try:
                print(f"Пытаюсь авторизоваться под аккаунтом: {account}")
                cookie_path = settings.SESSION_INSTAGRAM_COOKIES_PATH + account + '.pkl'
                success = cookies_auth(driver=self.driver, cookie_path=cookie_path)
                if success:
                    print(f"Успешная авторизация под аккаунтом: {account}")
                    return self.driver
                else:
                    print(f"Авторизация не удалась для аккаунта {account}.")
                    self.current_index += 1
            except Exception as e:
                print(f"Ошибка авторизации аккаунта {account}: {e}")
                self.current_index += 1
            account = self.get_current_account()

        self.close_current_driver()
        raise Exception("Все аккаунты недоступны для авторизации.")
