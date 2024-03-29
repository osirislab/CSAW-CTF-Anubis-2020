PERSISTENT_SERVICES := db traefik redis
RESTART_ALWAYS_SERVICES := anubis-api anubis-web pipeline-api
PUSH_SERVICES := anubis-api anubis-web
BUILD_ALLWAYS := anubis-api anubis-web pipeline-api


CURRENT_DIR := $(shell basename $$(pwd) | tr '[:upper:]' '[:lower:]')
IMAGES := $(shell \
	ruby -ryaml -rjson -e 'puts JSON.pretty_generate(YAML.load(ARGF))' \
	docker-compose.yml | jq '.services | .[].image | select(.!=null)' -r \
	2> /dev/null \
)
BUILT_IMAGES := $(shell \
	docker image ls | \
	awk '{print $$1}' | \
	grep -P '^($(CURRENT_DIR)_|os3224-)' \
	2> /dev/null \
)
RUNNING_CONTAINERS := $(shell docker-compose ps -q)
API_IP := $(shell docker network inspect anubis_default | \
	jq '.[0].Containers | .[] | select(.Name == "anubis_api_1") | .IPv4Address' -r | \
	awk '{print substr($$0, 1, index($$0, "/")-1)}' \
	2> /dev/null \
)
VOLUMES := $(shell docker volume ls | awk '{if (match($$2, /^anubis_.*$$/)) {print $$2}}')


help:
	@echo 'For convenience'
	@echo
	@echo 'Available make targets:'
	@grep PHONY: Makefile | cut -d: -f2 | sed '1d;s/^/make/'

.PHONY: check        # Checks that env vars are set
check:
	for var in ACME_EMAIL AUTH DOMAIN; do \
		if ([ -f .env ] && ! grep -P "^$${var}=" .env &> /dev/null) && [ ! -z "$${var}" ]; then \
			echo "ERROR $${var} not defined! this variable is required" 1>&2; \
		fi; \
	done

.PHONY: build        # Build all docker images
build:
	docker-compose build --parallel $(BUILD_ALLWAYS)
	./assignment/build.sh

.PHONY: debug        # Start the cluster in debug mode
debug: check build
	docker-compose up -d $(PERSISTENT_SERVICES)
	docker-compose up \
		-d --force-recreate \
		$(RESTART_ALWAYS_SERVICES)

yeetdb:
	docker-compose kill db
	docker-compose rm -f
	docker volume rm anubis_db_data
	docker-compose up -d --force-recreate db anubis-api

.PHONY: clean        # Clean up volumes, images and data
clean:
	docker-compose kill
	if [ -n "$(RUNNING_CONTAINERS)" ]; then \
		docker rm -f $(RUNNING_CONTAINERS); \
	fi
	if [ -n "$(IMAGES)" ]; then \
		docker rmi -f $(IMAGES); \
	fi
	if [ -n "$(BUILT_IMAGES)" ]; then \
		docker rmi -f $(BUILT_IMAGES); \
	fi
	if [ -n "${VOLUMES}" ]; then \
		docker volume rm $(VOLUMES); \
	fi
	docker system prune -f

	if [ -d web/node_modules ]; then rm -rf web/node_modules; fi
	if [ -d api/venv ]; then rm -rf api/venv; fi
