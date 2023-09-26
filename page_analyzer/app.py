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
from dotenv import load_dotenv
import validators
from urllib.parse import urlparse, urlunsplit
from datetime import datetime
from bs4 import BeautifulSoup


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


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def without_null(dict):
    for key in dict.keys():
        dict[key] = '' if dict[key] is None else dict[key]
    return dict


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
        query = '''
        SELECT urls.id, urls.name, MAX(url_checks.created_at) as last_check,
               url_checks.status_code
               FROM urls LEFT JOIN url_checks ON urls.id = url_checks.url_id
               GROUP BY urls.id, url_checks.status_code
               ORDER BY urls.created_at DESC
        '''
        data.execute(query)
        answer = data.fetchall()
        urls = [dict(row) for row in answer]

        urls_without_null = list(map(without_null, urls))
        # sort urls by 'id' in descending order
        urls_without_null.sort(
            reverse=True, key=lambda url: url.get('urls_id')
        )

    return render_template(
        'urls.html',
        urls=urls_without_null,
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
            'SELECT '
            'id, url_id, created_at, status_code, h1, title, description '
            'FROM url_checks WHERE url_id=%s',
            (str(id),)
        )
        answer = data.fetchall()
        url_checks = [dict(row) for row in answer]
        urls_without_null = list(map(without_null, url_checks))
        # sort checks by 'id' in descending order
        urls_without_null.sort(
            reverse=True, key=lambda url: url.get('id')
        )
    return render_template(
        'urls_add.html',
        message=message,
        id=id,
        name=name,
        created_at=created_at,
        url_checks=urls_without_null,
    )


# make check
@app.post("/urls/<id>/checks")
def make_check(id):
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as data:
        data.execute(
            'SELECT id, name, created_at FROM urls WHERE id=%s',
            (str(id),)
        )
        curr_url = data.fetchone()
        name = curr_url[1]
    # get response
    try:
        response = requests.get(name, verify=False)
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', category='alert-danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp
    success_status_codes = range(200, 300)
    if response.status_code not in success_status_codes:
        flash('Произошла ошибка при проверке', category='alert-danger')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp

    date_time = datetime.now().strftime("%Y-%m-%d")
    soup = BeautifulSoup(response.text, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = soup.find("meta", {"name": "description"})
    content = description['content'] if description else ''

    with conn.cursor() as db:
        db.execute(
            'INSERT INTO url_checks'
            '(url_id, created_at, status_code, h1, title, description) VALUES '
            '(%s, %s, %s, %s, %s, %s)',
            (str(id), date_time, str(response.status_code), h1, title, content)
        )
        conn.commit()

        flash('Страница успешно проверена', category='alert-success')
        resp = make_response(redirect(url_for('get_curr_url', id=id)))
        resp.headers['X-ID'] = id
        return resp
