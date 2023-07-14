.PHONY: clean clean-build clean-pyc clean-test coverage dist docs help install lint lint/flake8 lint/black \
build-postgres run-postgres create-db drop-db
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"
POSTGRES_DATA_PATH := "/mnt/external2/data"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint/flake8: ## check style with flake8
	flake8 epilepsiae_sql_dataloader tests
lint/black: ## check style with black
	black --check epilepsiae_sql_dataloader tests

lint: lint/flake8 lint/black ## check style

test: ## run tests quickly with the default Python
	pytest

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source epilepsiae_sql_dataloader -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/epilepsiae_sql_dataloader.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ epilepsiae_sql_dataloader
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install


### POSTGRESQL SECTION

IMAGE_NAME := seizure_db_image
CONTAINER_NAME := seizure_db
USERNAME := postgres

build-postgres:
	docker build -t $(IMAGE_NAME) .

run-postgres: build-postgres
	docker run -d --name $(CONTAINER_NAME) \
	  -p 5432:5432 \
	  -v $(POSTGRES_DATA_PATH):/var/lib/postgresql/data \
	  --restart always \
	  $(IMAGE_NAME)

create-db:
	docker exec -it -e PGPASSWORD=postgres $(CONTAINER_NAME) psql -U $(USERNAME) -c "CREATE DATABASE $(CONTAINER_NAME);"

create-test-db:
	docker exec -it -e PGPASSWORD=postgres $(CONTAINER_NAME) psql -U $(USERNAME) -c "CREATE DATABASE $(CONTAINER_NAME)_test;"

drop-db:
	docker exec -it -e PGPASSWORD=postgres $(CONTAINER_NAME) psql -U $(USERNAME) -c "DROP DATABASE $(CONTAINER_NAME);"

drop-test-db:
	docker exec -it -e PGPASSWORD=postgres $(CONTAINER_NAME) psql -U $(USERNAME) -c "DROP DATABASE $(CONTAINER_NAME)_test;"
