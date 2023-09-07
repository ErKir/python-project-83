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

import psycopg2
import psycopg2.extras
from dotenv import dotenv_values
import validators
from urllib.parse import urlparse, urlunsplit
import datetime

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

    valid_url = validators.url(cleaned_url)
    valid_len_url = validators.length(cleaned_url, max=255)

    if (valid_len_url and valid_url):
        conn = psycopg2.connect(DATABASE_URL)
        date_time = datetime.datetime.now().strftime("%Y-%m-%d")
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
# нет флеш, с невалидным урл
    message['message'] = 'Некорректный URL'
    message['type'] = 'alert-danger'
    flash(message['message'], category=message['type'])
    return render_template(
        'urls.html',
        message=message,
    )


# list urls to "/urls"
@app.get('/urls')
def urls_get():

    conn = psycopg2.connect(DATABASE_URL)
    messages = get_flashed_messages(with_categories=True)
    print('messages from urls GET- ', messages)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
        data.execute('SELECT * FROM urls')
        answer = data.fetchall()
        urls = [dict(row) for row in answer]
    return render_template(
        'urls.html',
        urls=urls,
        messages=messages,
    )


@app.route("/urls/<id>")
def get_curr_url(id):
    message = get_flashed_messages(with_categories=True)
    print('messages from get_curr_url- ', message)
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as data:
        data.execute(
            'SELECT id, name, created_at FROM urls WHERE id=%s',
            (str(id),)
        )
        curr_url = data.fetchone()
        dic = {}
        name = curr_url[1]
        created_at = curr_url[2]
        dic['id'] = id
        dic['name'] = name
        dic['created_at'] = created_at
    return render_template(
        'urls_add.html',
        message=message,
        id=dic['id'],
        name=dic['name'],
        created_at=dic['created_at']
    )

# 2023-08-07
