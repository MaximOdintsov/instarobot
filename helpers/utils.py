import re
from urllib.parse import urlparse, parse_qs


def extract_original_link(raw_link):
    """
    Функция извлекает оригинальную ссылку
    """    
    parsed_url = urlparse(raw_link)
    query_params = parse_qs(parsed_url.query)
    orig_link = query_params.get("u", [""])[0]
    if orig_link:
        
        return query_params.get("u", [""])[0]
    return raw_link


def parse_activity_data(data_list: list) -> dict:
    """
    Функция распределения списка основной информации об аккаунте
    """
    def parse_number_accurate(text: str) -> int:
        """
        Функция для преобразования текста в числовой формат
        """
        number_map = {
            'тыс.': 1000,
            'млн': 1000000,
            'млн.': 1000000
        }
        number = re.findall(r'[\d\s,]+', str(text))
        multiplier = 1
        for key, value in number_map.items():
            if key in text:
                multiplier = value
                break
        if number:
            clean_number = number[0].replace(' ', '').replace(',', '.')
            return int(float(clean_number) * multiplier)
        return 0
    

    result = {'posts': 0, 'subscribers': 0, 'subscriptions': 0}
    for item in data_list:
        if 'публикац' in item:
            result['posts'] = parse_number_accurate(item)
        elif 'подписчик' in item:
            result['subscribers'] = parse_number_accurate(item)
        elif any(word in item for word in ['подписок', 'подписки', 'подписка']):
            result['subscriptions'] = parse_number_accurate(item)
    return result