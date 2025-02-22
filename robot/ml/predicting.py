import joblib
import pandas as pd
import numpy as np
from robot.database.models import AccountType
from robot.conf import settings


def get_account_type(data: pd.DataFrame, threshold: float = 0.8) -> AccountType:
    """
    Предсказывает и возвращает тип аккаунта
    """
    loaded_model = joblib.load(settings.ACCOUNT_TYPE_MODEL_PATH)
    
    preds = loaded_model.predict(data)  # Предсказанные классы
    probs = loaded_model.predict_proba(data)  # Вероятности классов

    # Индекс предсказанного класса
    pred_index = np.argmax(probs[0])  # Максимальная вероятность в первой строке

    # Проверяем вероятность
    prob_percent = probs[0][pred_index]
    print(f'Предсказанный класс: "{preds[0]}". Вероятность класса: "{prob_percent}"')
    if prob_percent < threshold:  # Если вероятность меньше threshold (в %)
        return AccountType.UNKNOWN  # Назначаем тип UNKNOWN
    else:
        return AccountType(preds[0])  # Преобразуем строку в enum
