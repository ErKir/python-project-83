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
	pip install --upgrade pip && pip install poetry
	poetry install

DATABASE_URL ?= postgres://page_analyzer_sm2u_user:XbskxoQT7ZHCLu8BAL6qWrIwRT8DC6G8@dpg-cirdidtgkuvqadqogel0-a.oregon-postgres.render.com/page_analyzer_sm2u
database:
	psql -a -d $(DATABASE_URL) -f database.sql

build: install database

# PGPASSWORD=XbskxoQT7ZHCLu8BAL6qWrIwRT8DC6G8 psql -h dpg-cirdidtgkuvqadqogel0-a.oregon-postgres.render.com -U page_analyzer_sm2u_user page_analyzer_sm2u