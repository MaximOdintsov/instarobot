import re
import string
from urllib.parse import urlparse
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class TextCleaner(BaseEstimator, TransformerMixin):
    """
    Кастомный трансформер, который применяет text_preprocessing 
    к каждому элементу входного массива/Series.
    """
    def fit(self, X, y=None):
        return self

    def text_preprocessing(self, text: str) -> str:
        """
        Выполняет следующие шаги:
        - Удаление эмодзи
        - Удаление ссылок
        - Приведение к нижнему регистру
        - Удаление пунктуации
        - Лемматизация
        - Удаление лишних пробелов
        """
        text = str(text)
        # Удаляем эмодзи
        text = re.sub(r'[^\w\s.,;:!?@#№$%()\-\u0400-\u04FF]', '', text)

        # Удаляем/заменяем ссылки
        text = re.sub(r'http\S+|www.\S+|youtu\S+', '', text)
        
        # Приведение к нижнему регистру
        text = text.lower()
        
        # Удаление пунктуации
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Удаление лишних пробелов и переносов
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text or ''
    
    def transform(self, X, y=None):
        # На случай, если X — не Series, приводим к Series
        # и заполнем пропуски пустыми строками
        X = pd.Series(X).fillna("")
        return X.apply(self.text_preprocessing).values


class DomainBinarizer(BaseEstimator, TransformerMixin):
    """
    Превращает список ссылок в набор бинарных фич:
    для каждого уникального домена из обучающей выборки
    создаётся отдельная колонка (0 или 1).
    """
    def __init__(self):
        pass

    def fit(self, X, y=None):
        # Собираем все уникальные домены
        all_domains = set()
        for row in X:
            if isinstance(row, list):
                for link in row:
                    domain = self._extract_domain(link)
                    if domain:
                        all_domains.add(domain)
        self.all_domains_ = sorted(all_domains)
        return self

    def transform(self, X):
        # Для каждой строки генерируем вектор из 0 и 1
        # в соответствии со списком self.all_domains_
        output = []
        for row in X:
            # Сформируем словарь вида {домен: 0 или 1}
            row_dict = dict.fromkeys(self.all_domains_, 0)
            if isinstance(row, list):
                for link in row:
                    domain = self._extract_domain(link)
                    if domain and domain in row_dict:
                        row_dict[domain] = 1
            output.append(row_dict)
        # Превратим список словарей в DataFrame
        return pd.DataFrame(output, columns=self.all_domains_)

    def _extract_domain(self, link):
        # Вырезаем домен (без поддоменов) из URL
        try:
            parsed_url = urlparse(link)
            domain = parsed_url.netloc
            parts = domain.split('.')
            if len(parts) > 2:
                domain = '.'.join(parts[-2:])
            return domain if domain else None
        except:
            return None


