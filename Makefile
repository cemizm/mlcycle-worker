.DEFAULT_GOAL := worker

image = cemizm/mlcycle_worker
tag = 0.1

.PHONY: build
build:
	docker build -t $(image):$(tag) -f Dockerfile .

.PHONY: cli
cli: build
	docker run -it --rm $(image):$(tag) /bin/bash

.PHONY: dev
dev: build
	docker run -it --rm $(image):$(tag) /bin/sleep infinity

.PHONY: publish
publish: build
	docker tag $(image):$(tag) $(image):latest
	docker push $(image):$(tag)
	docker push $(image):latest