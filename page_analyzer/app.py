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
import validators
from urllib.parse import urlparse, urlunsplit

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


# maybe move to another module?
def is_valid_url(url):
    valid_url = validators.url(url)
    valid_len_url = validators.length(url, max=255)
    if (valid_len_url and valid_url):
        return True
    return False


def parse_url(data):
    url_obj = urlparse(data['url'])
    return urlunsplit((url_obj.scheme, url_obj.netloc, '', '', '',))


@app.route("/")
def index():
    return render_template('index.html')


# url add
@app.post("/urls")
def url():
    data = request.form.to_dict()
    parsed_url = parse_url(data)
    if is_valid_url(parsed_url):
        id, message = add_url(parsed_url)
        flash(*message)
        resp = redirect(url_for('get_curr_url', id=id), code=302)
        resp.headers['X-ID'] = id
        return resp
    flash('Некорректный URL', 'danger')
    return render_template('urls.html'), 422


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
        id, name, created_at, urls
    ) = get_url_info(id)

    return render_template(
        'urls_add.html',
        id=id,
        name=name,
        created_at=created_at,
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
        resp.headers['X-ID'] = id
        return resp

    message = add_check(id, response)
    flash(*message)
    resp = make_response(redirect(url_for('get_curr_url', id=id)))
    resp.headers['X-ID'] = id
    return resp
