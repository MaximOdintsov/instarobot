from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium_management import start_driver, open_link, get_wait_element, get_wait_elements, close_driver


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