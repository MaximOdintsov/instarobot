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