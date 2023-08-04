#!/usr/bin/env python3

import os
from flask import Flask, render_template
import psycopg2
from dotenv import dotenv_values


config = dotenv_values(".env")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    return render_template('index.html')


DATABASE_URL = config['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL)
