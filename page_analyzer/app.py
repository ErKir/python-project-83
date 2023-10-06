#!/usr/bin/env python3

import os
from flask import (
    Flask,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
import requests
from dotenv import load_dotenv
from page_analyzer.utils import validate
from page_analyzer.utils import parse_url

from page_analyzer.db import (
    add_url,
    get_urls as get_urls_from_db,
    get_url_info,
    get_url_by_id,
    add_check,
    find_url_id,
    connect,
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
connection = connect()


@app.route("/")
def index():
    return render_template('index.html')


@app.post("/urls")
def url():
    data = request.form.to_dict()
    parsed_url = parse_url(data)
    validation_errors = validate(parsed_url)
    if validation_errors:
        flash('Некорректный URL', 'danger')
        return render_template(
            'urls.html',
        ), 422
    found_id = find_url_id(parsed_url, connection)
    if found_id:
        flash('Страница уже существует', 'info')
        resp = redirect(url_for('get_curr_url', id=found_id[0]), code=302)
        return resp
    added_url_id = add_url(parsed_url, connection)
    flash('Страница успешно добавлена', 'success')
    resp = redirect(url_for('get_curr_url', id=added_url_id), code=302)
    return resp


@app.get('/urls')
def get_urls():
    urls = get_urls_from_db(connection)
    return render_template(
        'urls.html',
        urls=urls,
    )


@app.route("/urls/<id>")
def get_curr_url(id):
    (
        id, curr_url, urls
    ) = get_url_info(id, connection)

    return render_template(
        'urls_add.html',
        id=id,
        curr_url=curr_url,
        url_checks=urls,
    )


@app.post("/urls/<id>/checks")
def make_check(id):
    curr_url = get_url_by_id(id, connection)
    name = curr_url[0]
    success_status_codes = range(200, 300)

    try:
        response = requests.get(name, verify=False)
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', category='danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        return resp

    if response.status_code not in success_status_codes:
        flash('Произошла ошибка при проверке', category='danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        return resp

    add_check_is_successful = add_check(id, response, connection)
    if add_check_is_successful:
        message = ('Страница успешно проверена', 'success')
    else:
        message = ('Произошла ошибка записи проверки', 'danger')
    flash(*message)
    resp = make_response(redirect(url_for('get_curr_url', id=id)))
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
