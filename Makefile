INSTA_PREFIX=insta

.PHONY: docker-up docker-down

# Запускаем контейнеры в фоне
docker-up:
	docker compose up -d

# Останавливаем и удаляем контейнеры
docker-down:
	docker compose down

post-links:
	./main.py post_links_parser --max-scrolls=1

table:
	./main.py google_table

run: docker-up
	screen -mdS ${INSTA_PREFIX}_post_links ./main.py post_links_parser --max-scrolls=500
	screen -mdS ${INSTA_PREFIX}_post_data_1 ./main.py post_data_parser
	screen -mdS ${INSTA_PREFIX}_post_data_2 ./main.py post_data_parser
	screen -mdS ${INSTA_PREFIX}_post_data_3 ./main.py post_data_parser -ids 1 -ids 2 -ids 3
	screen -mdS ${INSTA_PREFIX}_account_data_1 ./main.py account_data_parser
	screen -mdS ${INSTA_PREFIX}_account_data_2 ./main.py account_data_parser
	screen -mdS ${INSTA_PREFIX}_account_data_3 ./main.py account_data_parser -ids 1 -ids 2 -ids 3
	screen -mdS ${INSTA_PREFIX}_postprocess_account ./main.py postprocess_account_data

stop: docker-down
	screen -ls | grep ${INSTA_PREFIX} | cut -d. -f1 | awk '{print $$1}' | xargs -r kill