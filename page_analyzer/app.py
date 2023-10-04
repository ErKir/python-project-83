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
from page_analyzer.scripts.validator import is_valid_url
from page_analyzer.scripts.parser import parse_url

from page_analyzer.model import (
    add_url,
    get_urls as get_urls_from_db,
    get_url_info,
    get_url_by_id,
    add_check,
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    return render_template('index.html')


# url add
@app.post("/urls")
def url():
    data = request.form.to_dict()
    parsed_url = parse_url(data)
    validation_errors = is_valid_url(parsed_url)
    if validation_errors:
        flash('Некорректный URL', 'danger')
        return render_template(
            'urls.html',
            errors=validation_errors
        ), 422
    id, message = add_url(parsed_url)
    flash(*message)
    resp = redirect(url_for('get_curr_url', id=id), code=302)
    return resp


# list urls to "/urls"
@app.get('/urls')
def get_urls():
    urls = get_urls_from_db()
    return render_template(
        'urls.html',
        urls=urls,
    )


@app.route("/urls/<id>")
def get_curr_url(id):
    (
        id, curr_url, urls
    ) = get_url_info(id)

    return render_template(
        'urls_add.html',
        id=id,
        curr_url=curr_url,
        url_checks=urls,
    )


# make check
@app.post("/urls/<id>/checks")
def make_check(id):
    curr_url = get_url_by_id(id)
    name = curr_url[0]
    # get response
    try:
        response = requests.get(name, verify=False)
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', category='danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp
    success_status_codes = range(200, 300)
    if response.status_code not in success_status_codes:
        flash('Произошла ошибка при проверке', category='danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        return resp

    message = add_check(id, response)
    flash(*message)
    resp = make_response(redirect(url_for('get_curr_url', id=id)))
    return resp


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
