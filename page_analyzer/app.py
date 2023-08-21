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
        with conn.cursor() as data:
            data.execute(
                'SELECT id, name, created_at FROM urls WHERE name=%s',
                (cleaned_url,)
            )
            curr_url = data.fetchall()[0]
            id = curr_url[0]
            # name = curr_url[1]
            # created_at = curr_url[2].strftime("%Y-%m-%d")
            # dic['id'] = id
            # dic['name'] = name
            # # 2023-08-07
            # dic['created_at'] = created_at
            # print('dic_url==', dic)
            # flash('Страница успешно добавлена', 'success')
        conn.close()
        return make_response(redirect(url_for('get_curr_url', id=id)))

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


@app.route("/urls/<id>")
def get_curr_url(id):
    print('hi from urls get! looser! id=', id)

    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as data:
        data.execute(
            'SELECT * FROM urls'
            # 'SELECT id, name, created_at FROM urls WHERE id=%s',
            # (str(id),)
        )
        curr_url = data.fetchone()
        print('curr_url==', curr_url)
        dic = {}
        name = curr_url[1]
        created_at = curr_url[2].strftime("%Y-%m-%d")
        dic['id'] = id
        dic['name'] = name
        dic['created_at'] = created_at
    return render_template(
        'urls_add.html',
        id=dic['id'],
        name=dic['name'],
        created_at=dic['created_at']
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
