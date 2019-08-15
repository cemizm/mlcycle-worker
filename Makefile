.DEFAULT_GOAL := worker

.PHONY: worker.dev
worker.dev:
	docker-compose run -d --name worker.dev worker /bin/sleep infinity

.PHONY: worker.cli
worker.cli:
	docker exec -it worker.dev /bin/bash

.PHONY: worker
worker:
	docker-compose up -d worker

.PHONY: teardown
teardown:
	docker-compose down