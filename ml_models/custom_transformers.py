import re
import string
from urllib.parse import urlparse
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd


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
    

class DomainExtractor(BaseEstimator, TransformerMixin):
    """
    Трансформер, рассчитанный на то, что на вход приходит одна колонка (Series).
    """
    def fit(self, X, y=None):
        return self
    
    def extract_domains(self, link_str):
        """Извлечение домена из URL"""
        if not link_str:
            return ""
        links = link_str.split('\n')
        domains = []
        for link in links:
            try:
                parsed_url = urlparse(link)
                domain = parsed_url.netloc
                # Удаление поддоменов
                domain_parts = domain.split('.')
                if len(domain_parts) > 2:
                    domain = '.'.join(domain_parts[-2:])
                domains.append(domain)
            except Exception:
                pass  # Игнорировать некорректные URL
        return ' '.join(domains)
    
    def transform(self, X):
        # Предположим, что X — это pd.Series.
        # Если X вдруг будет массивом NumPy, нужно превратить в Series.
        if not isinstance(X, pd.Series):
            X = pd.Series(X)
        return X.apply(self.extract_domains)  # Вернём Series со строками-доменами