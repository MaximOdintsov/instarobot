INSTA_PREFIX=insta

.PHONY: rabbit-up rabbit-down

# Запускаем контейнеры в фоне
rabbit-up:
	cd services/rabbitmq && docker compose up -d

# Останавливаем и удаляем контейнеры
rabbit-down:
	cd services/rabbitmq && docker compose down

post-links:
	./manage.py post_links_parser --max-scrolls=1

table:
	./manage.py google_table

run: rabbit-up
	screen -mdS ${INSTA_PREFIX}_post_links ./manage.py post_links_parser --max-scrolls=200
	screen -mdS ${INSTA_PREFIX}_post_data_1 ./manage.py post_data_parser -ids 0
	screen -mdS ${INSTA_PREFIX}_post_data_2 ./manage.py post_data_parser -ids 1
	screen -mdS ${INSTA_PREFIX}_post_data_3 ./manage.py post_data_parser -ids 2
	screen -mdS ${INSTA_PREFIX}_post_data_5 ./manage.py post_data_parser -ids 4
	screen -mdS ${INSTA_PREFIX}_post_data_6 ./manage.py post_data_parser -ids 5
	screen -mdS ${INSTA_PREFIX}_post_data_4 ./manage.py post_data_parser -ids 3
	screen -mdS ${INSTA_PREFIX}_postprocess_account ./manage.py postprocess_account_data

stop:
	screen -ls | grep ${INSTA_PREFIX} | cut -d. -f1 | awk '{print $$1}' | xargs -r kill