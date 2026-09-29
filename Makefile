.PHONY: up down run-queries clean

up:
	docker-compose up -d
	@echo "Waiting for MySQL to initialize..."
	@sleep 15

run-queries:
	@mkdir -p outputs
	docker-compose exec -T mysql mysql -uroot -proot ecommerce_analytics < sql/02_funnel_metrics.sql > outputs/02_funnel_metrics.csv
	docker-compose exec -T mysql mysql -uroot -proot ecommerce_analytics < sql/03_time_to_convert.sql > outputs/03_time_to_convert.csv
	docker-compose exec -T mysql mysql -uroot -proot ecommerce_analytics < sql/04_country_segmentation.sql > outputs/04_country_segmentation.csv
	@echo "Queries executed. Results saved to outputs/"

down:
	docker-compose down -v

clean: down
	rm -rf outputs/
