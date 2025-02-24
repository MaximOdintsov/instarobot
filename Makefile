.PHONY: rabbit-up rabbit-down

# Запускаем контейнеры в фоне
rabbit-up:
	cd services/rabbitmq && docker compose up -d

# Останавливаем и удаляем контейнеры
rabbit-down:
	cd services/rabbitmq && docker compose down

post-links:
	./manage.py post_links_parser --max-scrolls=1
