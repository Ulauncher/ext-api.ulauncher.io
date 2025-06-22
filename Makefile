.ONESHELL:
.PHONY: help all test format ruff pytest clone-prod-db upgrade-deps

SHELL := /bin/bash

export AUTH0_DOMAIN=ulauncher.auth0.com
export AUTH0_CLIENT_ID=AUTH0_CLIENT_ID
export AUTH0_CLIENT_SECRET=AUTH0_CLIENT_SECRET
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
export AWS_DEFAULT_REGION=nyc3
export EXTENSIONS_TABLE_NAME=EXTENSIONS_TABLE_NAME
export EXT_IMAGES_BUCKET_NAME=EXT_IMAGES_BUCKET_NAME
export PYTHONPATH=$(shell pwd)
export MONGODB_CONNECTION=mongodb://mongodb:27017/
export DB_NAME=ext_api_dev

TARGETS = db_migrations ext_api tests

help: # Shows this list of available actions (targets)
	@# Only includes targets with comments, but not if they have Commands with two ## chars
	sed -nr \
		-e 's|^#=(.*)|\n\1:|p' \
		-e 's|^([a-zA-Z-]*):([^#]*?\s# (.*))| \1\x1b[35m - \3\x1b[0m|p' \
		$(lastword $(MAKEFILE_LIST)) \
		| expand -t20

all: test

test: ruff pytest # Run all tests

ruff: # Run code style and formatting checks with ruff
	@echo
	@echo '[ test: ruff ]'
	@ruff check $(TARGETS) && ruff format --check $(TARGETS)

format: # Format code with ruff
	@echo
	@echo '[ format: ruff ]'
	@ruff format $(TARGETS)

pytest: # Run unit tests with pytest
	@echo
	@echo '[ test: pytest ]'
	@py.test $(TARGETS) tests

clone-prod-db:
	@set -ex; \
	prodUrl="mongodb+srv://ulauncher:xxx@dbhost/ext_api_prod"; \
	mongosh $$prodUrl --quiet --eval "db.getCollectionNames().join('\n')" > collections.txt; \
	mkdir -p /tmp/dbdump; \
	while read coll; do \
		mongoexport --uri="$$prodUrl" --collection="$$coll" --out="/tmp/dbdump/$${coll}.json"; \
	done < collections.txt; \
	find /tmp/dbdump -type f -name '*.json' -exec sed -i 's/prod\.nyc3/dev.fra1/g' {} +; \
	for f in /tmp/dbdump/*.json; do \
		coll=$$(basename "$$f" .json); \
		mongoimport --uri="mongodb+srv://ulauncher-local:xxx@dbhost/ext_api_dev" --collection="$$coll" --file="$$f"; \
	done

upgrade-deps: # Upgrade Python dependencies to the latest versions (may break compatibility)
	@set -e; \
	python -m venv .venv; \
	. .venv/bin/activate; \
	pip install --upgrade -r <(sed 's/[=<>!].*//' requirements.txt); \
	pip freeze | grep -Ff <(sed 's/[=<>!].*//' requirements.txt) > tmp_requirements.txt && mv tmp_requirements.txt requirements.txt
	pip install --upgrade -r <(sed 's/[=<>!].*//' requirements.dev.txt); \
	pip freeze | grep -Ff <(sed 's/[=<>!].*//' requirements.dev.txt) > tmp_requirements.txt && mv tmp_requirements.txt requirements.dev.txt
