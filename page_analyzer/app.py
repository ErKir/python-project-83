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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    return render_template('index.html')


config = dotenv_values("env_vars.env")
DATABASE_URL = config['DATABASE_URL']


@app.post("/urls")
def url():
    errors = []
    data = request.form.to_dict()
    url_obj = urlparse(data['url'])
    print('url obj  - ', url_obj.scheme, url_obj.netloc)
    # найти как получать доступ к именованным членам
    # кортежа (scheme='https', netloc='www.сайт.by', )
    cleaned_url = urlunsplit((url_obj.scheme, url_obj.netloc, '', '', '',))
    print('given url is  - ', cleaned_url)
    valid_url = validators.url(cleaned_url)
    valid_len_url = validators.length(cleaned_url, max=255)
    if (valid_len_url and valid_url):
        conn = psycopg2.connect(DATABASE_URL)
        date_time = datetime.datetime.now()
        with conn.cursor() as db:
            db.execute(
                'INSERT INTO urls (name, created_at) VALUES (%s, %s)',
                (cleaned_url, date_time)
            )
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
            data.execute(
                'SELECT id, name, created_at FROM urls WHERE name=%s',
                (cleaned_url,)
            )
            curr_url = data.fetchall()
            print('curr_url==', curr_url)
        return render_template(
            'urls.html',
            id=curr_url['id'],
            name=curr_url['name'],
            created_at=url['created_at']
        )
    errors = valid_url if valid_len_url is True else valid_len_url
    return render_template(
        'urls.html',
        errors=errors
    )


# выводит список сайтов на "/urls"
@app.get('/urls')
def urls_get():
    conn = psycopg2.connect(DATABASE_URL)
    messages = get_flashed_messages(with_categories=True)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
        data.execute('SELECT * FROM urls')
        urls = data.fetchall()
    return render_template(
        'urls.html',
        urls=urls,
        messages=messages,
    )


# Страница успешно добавлена
# 2023-08-07

# @app.post('/posts')
# def posts_post():
#     repo = PostsRepository()
#     data = request.form.to_dict()
#     errors = validate(data)
#     if errors:
#         return render_template(
#             'posts/new.html',
#             post=data,
#             errors=errors,
#             ), 422
#     id = repo.save(data)
#     flash('Post has been created', 'success')
#     resp = make_response(redirect(url_for('posts_get')))
#     resp.headers['X-ID'] = id
#     return resp
