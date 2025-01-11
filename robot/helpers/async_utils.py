import aiohttp


async def async_shorten_isgd(session: aiohttp.ClientSession, url: str) -> str:
    """
    Сокращает ссылку через сервис is.gd.
    """
    api_url = f"https://is.gd/create.php?format=simple&url={url}"
    async with session.get(api_url) as response:
        text = await response.text()
        if "Error" in text:
            raise Exception(f"is.gd вернул ошибку: {text}")
        return text.strip()


async def async_shorten_tinyurl(session: aiohttp.ClientSession, url: str) -> str:
    """
    Сокращает ссылку через сервис tinyurl.
    """
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    async with session.get(api_url) as response:
        text = await response.text()
        if "Error" in text:
            raise Exception(f"tinyurl вернул ошибку: {text}")
        return text.strip()


async def url_shortening_async(url: str, session: aiohttp.ClientSession, logs: bool = False) -> str:
    """
    Асинхронная функция, которая пытается сократить ссылку сначала через is.gd,
    а в случае ошибки — через tinyurl.
    """
    url = str(url)
    try:
        return await async_shorten_isgd(session, url)
    except Exception as e:
        try:
            return await async_shorten_tinyurl(session, url)
        except Exception as e2:
            if logs:
                print(f'Ошибка при сокращении ссылки "{url}": {e2}')
            return url
        
