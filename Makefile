dev:
	poetry run flask --app page_analyzer:app run --debug --port 8000

lint:
	poetry run flake8 page_analyzer

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install --user dist/*.whl

package-test:
	poetry run pytest -vv

test-coverage:
	poetry run pytest --cov=page_analyzer --cov-report xml

PORT ?= 8000
start:
	poetry run gunicorn --reload -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

install:
	pip install --upgrade pip && pip install poetry
	poetry install

DATABASE_URL ?= postgres://kirill:esCiUzF9X4l73RaYn74wrnBoKDl5BMNs@dpg-cjb28k9itvpc73ddob4g-a/page_analyzer_tx40
database:
	psql -a -d $(DATABASE_URL) -f database.sql

build: install database
