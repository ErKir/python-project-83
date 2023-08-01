dev:
	poetry run flask --app page_analyzer:app run

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
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

install:
	pip install --upgrade poetry && poetry build && poetry install

build: install
