#!/usr/bin/env python3

import os
from flask import (
    Flask,
    flash,
    get_flashed_messages,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
import requests
import psycopg2
import psycopg2.extras
from dotenv import dotenv_values
import validators
from urllib.parse import urlparse, urlunsplit
from datetime import datetime


def is_valid_url(url):
    valid_url = validators.url(url)
    valid_len_url = validators.length(url, max=255)
    if (valid_len_url and valid_url):
        return True
    return False


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12)


@app.route("/")
def index():
    return render_template('index.html')


config = dotenv_values("env_vars.env")
DATABASE_URL = config['DATABASE_URL']


# url add
@app.post("/urls")
def url():
    message = {
        'message': 'Страница успешно добавлена',
        'type': 'alert-success',
    }
    data = request.form.to_dict()
    url_obj = urlparse(data['url'])
    cleaned_url = urlunsplit((url_obj.scheme, url_obj.netloc, '', '', '',))
    if is_valid_url(cleaned_url):
        conn = psycopg2.connect(DATABASE_URL)
        date_time = datetime.now().strftime("%Y-%m-%d")
        with conn.cursor() as db:
            try:
                db.execute(
                    'INSERT INTO urls (name, created_at) VALUES (%s, %s)',
                    (cleaned_url, date_time)
                )
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                message['message'] = 'Страница уже существует'
                message['type'] = 'alert-info'
                conn.rollback()

        with conn.cursor() as data:
            data.execute(
                'SELECT id, name, created_at FROM urls WHERE name=%s',
                (cleaned_url,)
            )
            curr_url = data.fetchall()[0]
            id = curr_url[0]
        conn.close()
        flash(message['message'], category=message['type'])
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp
    message = [('alert-danger', 'Некорректный URL')]
    return render_template(
        'urls.html',
        message=message,
    )


# list urls to "/urls"
@app.get('/urls')
def urls_get():
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
        query = 'SELECT DISTINCT urls.id AS urls_id, '\
                'url_checks.created_at AS created_at, '\
                'url_checks.status_code AS status_code, '\
                'name FROM url_checks JOIN urls ON urls.id = url_checks.url_id'
        data.execute(query)
        answer = data.fetchall()
        urls = [dict(row) for row in answer]
        # sort urls by 'id' in descending order
        urls.sort(
            reverse=True, key=lambda url: url.get('urls_id')
        )

    return render_template(
        'urls.html',
        urls=urls,
    )


@app.route("/urls/<id>")
def get_curr_url(id):
    message = get_flashed_messages(with_categories=True)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as data:
        data.execute(
            'SELECT id, name, created_at FROM urls WHERE id=%s',
            (str(id),)
        )
        curr_url = data.fetchone()
        name = curr_url[1]
        created_at = curr_url[2]

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
        data.execute(
            'SELECT id, url_id, created_at, status_code '
            'FROM url_checks WHERE url_id=%s',
            (str(id),)
        )
        answer = data.fetchall()
        url_checks = [dict(row) for row in answer]
        # sort checks by 'id' in descending order
        url_checks.sort(
            reverse=True, key=lambda url: url.get('id')
        )
    return render_template(
        'urls_add.html',
        message=message,
        id=id,
        name=name,
        created_at=created_at,
        url_checks=url_checks,
    )


# make check
@app.post("/urls/<id>/checks")
def make_check(id):
    message = {
        'message': 'Страница успешно проверена',
        'type': 'alert-success',
    }
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as data:
        data.execute(
            'SELECT id, name, created_at FROM urls WHERE id=%s',
            (str(id),)
        )
        curr_url = data.fetchone()
        name = curr_url[1]
    # get response
    response = requests.get(name, verify=False)
    print('response = ', type(response.status_code))

    date_time = datetime.now().strftime("%Y-%m-%d")
    with conn.cursor() as db:
        db.execute(
            'INSERT INTO url_checks'
            '(url_id, created_at, status_code) VALUES (%s, %s, %s)',
            (str(id), date_time, str(response.status_code))
        )
        conn.commit()

        flash(message['message'], category=message['type'])
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp

# 2023-08-07
#
# <div class="alert alert-danger" role="alert">
# Произошла ошибка при проверке</div>
# <div class="alert alert-success" role="alert">Страница успешно проверена</div>
