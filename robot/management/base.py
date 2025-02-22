from typing import List, Dict

from robot.helpers.selenium_management import start_driver, close_driver
from robot.robot import auth


class MultiInstagramAccountDriver:
    """
    Класс, который создает driver и автоматически авторизуется в instagram.
    Зависит от функции robot.robot.auth
    """
    def __init__(self, accounts: List[Dict]):
        """
        accounts: список словарей с данными аккаунтов,
        например: [{"username": "user1", "password": "pass1"}, {"username": "user2", "password": "pass2"}, ...]
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
        Закрывает текущий драйвер, переключается на следующий аккаунт и создаёт новый драйвер.
        Если аккаунты закончились, выбрасывается исключение.
        """
        self.current_index += 1
        account = self.get_current_account()
        if not account:
            raise Exception("Нет доступных аккаунтов для авторизации.")
        return account

    def authenticate(self):
        """
        Закрывает старый драйвер.
        Пытается авторизоваться с текущим аккаунтом.
        Если авторизация не удалась или произошла ошибка, автоматически переключается на следующий аккаунт.
        Возвращает успешно авторизованный аккаунт и драйвер.
        """
        account = self.get_current_account()
        if not account:
            raise Exception("Нет аккаунтов для авторизации.")

        while account:
            self.close_current_driver()
            self.start_new_driver()
            try:
                print(f"Пытаюсь авторизоваться под аккаунтом: {account['username']}")
                success = auth(driver=self.driver, username=account['username'], password=account['password'])
                if success:
                    print(f"Успешная авторизация под аккаунтом: {account['username']}")
                    return account, self.driver
                else:
                    print(f"Авторизация не удалась для аккаунта {account['username']}.")
                    self.switch_account()
            except Exception as e:
                print(f"Ошибка авторизации аккаунта {account['username']}: {e}")
                self.switch_account()
            account = self.get_current_account()

        self.close_current_driver()
        raise Exception("Все аккаунты недоступны для авторизации.")
