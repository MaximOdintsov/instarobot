### Настройка робота
1) Записать данные аккаунтов в *data/incoming_data/auth_path.json* (**Сначала нужно убрать 2факторку и зайти в настраиваемый аккаунт самостоятельно в браузере**)
2) Шаблоны сообщений в *data/incoming_data/message_templates.json*
3) Шаблоны комментариев в *data/incoming_data/comment_templates.json*
4) Ссылки на аккаунты в *data/incoming_data/account_links.txt* (**1 строка - 1 ссылка**)
5) Настройки интервалов находятся в config.py: **ACCOUNT_BREAK_MIN_TIME**, **ACCOUNT_BREAK_MAX_TIME**, **ACTION_BREAK_MIN_TIME**, **ACTION_BREAK_MAX_TIME** 
---
### Запуск робота
Команда `./spam_robot --links-num=3 --is-follow --is-message --is-comment` (Описание каждого из параметров записано в spam_robot.py)