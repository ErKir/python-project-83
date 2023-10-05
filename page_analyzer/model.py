#!/usr/bin/env python3

import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def without_null(dict):
    for key in dict.keys():
        dict[key] = '' if dict[key] is None else dict[key]
    return dict


def connect():
    return psycopg2.connect(DATABASE_URL)


def find_url_id(url):
    conn = connect()
    with conn.cursor() as data:
        data.execute(
            'SELECT id FROM urls WHERE name=%s',
            (url,)
        )
        return data.fetchone()


def add_url(url):
    message = ('Страница успешно добавлена', 'success')
    conn = connect()
    date_time = datetime.now().strftime("%Y-%m-%d")
    id = find_url_id(url)
    if id:
        message = ('Страница уже существует', 'info')
    else:
        with conn.cursor() as data:
            data.execute(
                'INSERT INTO urls (name, created_at) VALUES (%s, %s)',
                (url, date_time)
            )
            conn.commit()
            id = find_url_id(url)
    conn.close()
    return (id[0], message)


def get_all(table):
    conn = connect()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as data:
        data.execute(f'SELECT * FROM {table} ORDER BY id DESC')
        answer = data.fetchall()
        conn.close()
    return [dict(row) for row in answer]


def get_latest_check(url_id):
    conn = connect()
    with conn.cursor() as data:
        data.execute('SELECT id, status_code, created_at'
                     ' FROM url_checks WHERE url_id=%s'
                     ' ORDER BY id DESC LIMIT 1',
                     (str(url_id),))
        return data.fetchone()


def get_urls():
    urls = get_all('urls')
    result = []
    for url in urls:
        curr_info = {}
        curr_info['id'] = url['id']
        curr_info['name'] = url['name']
        check = get_latest_check(url['id'])
        if not check:
            result.append(curr_info)
        else:
            curr_info['status_code'] = check[1]
            curr_info['last_check'] = check[2]
            result.append(curr_info)
    return result


def get_url_by_id(id):
    conn = connect()
    with conn.cursor() as data:
        data.execute(
            'SELECT name, created_at FROM urls WHERE id=%s',
            (str(id),)
        )
        curr_url = data.fetchone()
        conn.close()
    return curr_url


def get_url_info(id):
    curr_url = get_url_by_id(id)
    conn = connect()
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
        urls_without_null.sort(
            reverse=True, key=lambda url: url.get('id')
        )
    return (id, curr_url, urls_without_null)


def add_check(id, response):
    conn = connect()
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
        return True
