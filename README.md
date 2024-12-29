### Настройка робота
1) Записать данные аккаунтов в data/incoming_data/auth_path.json (**Сначала нужно убрать 2факторку и зайти в настраиваемый аккаунт самостоятельно в браузере**)
2) Записать шаблоны сообщений в data/incoming_data/message_templates.json
3) Записать ссылки на аккаунты в data/incoming_data/account_links.txt (**1 строка - 1 ссылка**)
4) Чтобы настроить интервал отправки сообщений, измени **ACCOUNTS_BREAK_MIN_TIME** и **ACCOUNTS_BREAK_MAX_TIME** в config.py (берется рандомное число в этом промежутке)
---
### Запуск робота
Команда `.venv/bin/python3 send_messages --message-num=3`

--message-num=3 означает, что с каждого аккаунта будет написано по *3* сообщения