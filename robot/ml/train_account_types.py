import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from robot.ml.custom_transformers import TextCleaner, DomainBinarizer


def train(file_path: str):
    ##################################
    # Шаг 1: Предобработка текста
    ##################################

    # Создание DataFrame
    file_path = 'data/modеls/train_data/merged_table.xlsx'
    df = pd.read_excel(file_path)

    # Замена пустых значений
    df.fillna(
        {   
            'Предсказанный тип аккаунта': 'OTHER',
            'Описание страницы': '',
            'Ссылки из описания': '', 
            'Ссылки из контактов': '',
            'Кол-во постов': 0
        }, 
        inplace=True
    )

    # 1 шаг: Замена имени столбца
    # 2 шаг: Удаление всех строк с типом "OTHER"
    df.rename(columns={"Предсказанный тип аккаунта": "Тип аккаунта"}, inplace=True)
    # df = df[df["Тип аккаунта"] != "OTHER"]

    # Заменяем значения столбца на 1, если не NaN, и на 0, если NaN
    # 1 шаг - замена на True и False
    # 2 шаг - замена на 1 и 0
    df['Почта существует'] = df['Найденная почта'].notna().astype(int)

    # Разделяем ссылки в строках через '\n'
    df['Ссылки из описания'] = df['Ссылки из описания'].str.split('\n')
    df['Ссылки из контактов'] = df['Ссылки из контактов'].str.split('\n')


    ##################################
    # Шаг 2: Делим на X и y + разделяем данные на обучающую и тестовую выборки
    ##################################
    X = df[[
        "Описание страницы",  # text
        "Ссылки из описания",  # text
        "Ссылки из контактов",  # text
        "Почта существует",  # 1/0
        "Кол-во постов",  # num
    ]]
    y = df["Тип аккаунта"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42
    )

    ##################################
    # Шаг 3: Настраиваем векторизацию и классификацию + cобираем Pipeline 
    ##################################

    # Создание ColumnTransformer для обработки каждого столбца
    preprocessor = ColumnTransformer(
        transformers=[
            (
                'desc_tfidf',  # Для текстовых значений 
                Pipeline([
                    ('text_cleaner', TextCleaner()),
                    ('tfidf', TfidfVectorizer(stop_words='english',  # Стоп-слова
                                            ngram_range=(1, 3),  # Использование триграмм
                                            max_features=1250,  # Увеличение числа признаков
                                            sublinear_tf=True)  # Использование логарифмического масштаба для частоты терминов
                    ),
                ]),
                'Описание страницы'
                
            ),
            (
                'desc_links_binarizer',
                Pipeline([
                    ('binarizer', DomainBinarizer())
                    # при желании можно добавить StandardScaler() —
                    # но для бинарных фич это обычно не критично
                ]),
                'Ссылки из описания'
            ),
            (
                'contact_links_binarizer',
                Pipeline([
                    ('binarizer', DomainBinarizer())
                ]),
                'Ссылки из контактов'
            ),
            (
                'binary', 
                'passthrough',  # Пропускает значения без изменений
                ['Почта существует']
            ),
            (
                'num_scaler', 
                StandardScaler(),  # Для числовых значений
                ['Кол-во постов']
            ),
        ],
        remainder='drop'  # Удаляет остальные столбцы, если они есть
    )


    ##################################
    # Шаг 4: Собираем Pipeline
    ##################################

    # Использование методов ресэмплинга
    pipeline = ImbPipeline([
        ('preprocessor', preprocessor),
        ('smote', SMOTE(random_state=42)),  # Увеличение числа примеров для редких классов с помощью методов, таких как SMOTE.
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000))  # 0.77
    ])

    # ##################################
    # # Шаг 5: Обучение и оценка
    # ##################################

    # Обучаем
    pipeline.fit(X_train, y_train)

    # Предсказываем
    y_pred = pipeline.predict(X_test)

    # Смотрим отчёт
    print(classification_report(y_test, y_pred, zero_division=0))
    
    return pipeline
    
    
def save_model(pipeline: ImbPipeline, model_path: str):
    joblib.dump(pipeline, model_path)
    print(f"Модель сохранена в файле {model_path}")


def check_model(model_path: str, test_df: pd.DataFrame):
    loaded_model = joblib.load(model_path)
    print(f"Модель загружена из файла {model_path}")
        
    preds = loaded_model.predict(test_df)
    print("Предсказанные классы:", preds)

    proba = loaded_model.predict_proba(test_df)
    print("Вероятности классов:", proba)