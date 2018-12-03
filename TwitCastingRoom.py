# -*- coding: utf-8 -*-
from datetime import datetime

import os
from flask import Flask, request, redirect, render_template, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.contrib.cache import SimpleCache
import requests
import json

from config import BASE64_ENCODED_STRING

app = Flask(__name__)
cache = SimpleCache()

db_uri = "sqlite:///" + os.path.join(app.root_path, 'flask_test.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class Channel(db.Model):
    __tablename__ = "channel"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.String(), nullable=False)
    url = db.Column(db.String(), nullable=False)

    def __init__(self, id, movie_id, url):
        self.id = id
        self.movie_id = movie_id
        self.url = url


BASE_URL = "https://apiv2.twitcasting.tv"
MOVIE_URL = BASE_URL + "/movies/{movie_id}"
USER_URL = BASE_URL + "/users/{user_id}"
SEARCH_URL = BASE_URL + "/search/lives"


HEADER = {"X-Api-Version": "2.0", "Authorization": "Basic %s" % BASE64_ENCODED_STRING.decode("utf-8")}


def get_recommend(n=10):
    res = requests.get(SEARCH_URL+"?limit={}&type=recommend&lang=ja".format(n), headers=HEADER)
    if res.status_code == 200:
        return json.loads(res.text)["movies"]
    return res.text


def get_user(screen_id):
    res = requests.get(USER_URL.format(user_id=screen_id), headers=HEADER)
    if res.status_code == 200:
        return json.loads(res.text)
    return res.text


def is_user_living(user):
    return user["user"]["is_live"]


def is_movie_living(movie):
    return movie["movie"]["is_live"]


def get_movie(movie_id):
    res = requests.get(MOVIE_URL.format(movie_id=movie_id), headers=HEADER)
    if res.status_code == 200:
        return json.loads(res.text)
    return res.text


def get_channel_movie_id(ch_id):
    # dbからchannel(index)のでーたを取る。なければNone
    for ch in Channel.query.all():
        if ch.id == ch_id:
            return ch.movie_id
    return None


def is_watching(movie_id):
    # dbにchannelとして存在するか
    for ch in Channel.query.all():
        if ch.movie_id == movie_id:
            return True
    return False


def set_watching(ch_id, movie_id, url):
    # dbにchannel,movie_id,urlを保存
    if ch_id in [ch.id for ch in Channel.query.all()]:
        ch = Channel.query.filter_by(id=ch_id).first()
        ch.movie_id = movie_id
        ch.url = url
    else:
        db.session.add(Channel(ch_id, movie_id, url))
    db.session.commit()


def last_movie_hls_url(user):
    last_movie_id = user["user"]["last_movie_id"]
    return get_movie(last_movie_id)["movie"]["hls_url"]


def get_hls_url(ch_id):
    movie_id = get_channel_movie_id(ch_id)
    if movie_id is not None:
        movie = get_movie(movie_id)
        print(movie)
        if "error" not in movie:
            if is_movie_living(movie):
                return movie["movie"]["hls_url"]
    for movie in get_recommend():

        if not is_watching(movie["movie"]["id"]):
            set_watching(ch_id, movie["movie"]["id"], movie["movie"]["link"])
            return movie["movie"]["hls_url"]
    raise ValueError


@app.route('/')
def hello_world():
    return render_template("index.html")


@app.route('/api')
def channel():
    if request.args.get('channel') is None:
        return redirect("/")
    try:
        n = int(request.args.get('channel'))
        n = n if 1 <= n <= 6 else 1
    except TypeError:
        n = 1
    except:
        raise
    url = get_hls_url(n) if n != 6 else "http://twitcasting.tv/app1e_s/metastream.m3u8/?video=1"
    resp = requests.get(url)
    print(resp.text.split('\n'))
    print()
    return Response(resp.content.decode('utf-8'), mimetype="application/vnd.apple.mpegurl")


@app.route('/hls_test')
def test_hls():
    un = cun = request.cookies.get('username')
    print(un)
    if un is None:
        un = "app1e_s"
    r = requests.get('http://twitcasting.tv/%s/metastream.m3u8/?video=1' % un)
    print(datetime.now())
    if r.content:
        u = r.content.decode('utf-8').split('\n')
        nr = requests.get(u[4])
        print(u)
        print(nr.status_code)
        print(nr.content.decode('utf-8').split('\n'))
    else:
        print("no m3u8")
    resp = Response(r.content.decode('utf-8'), mimetype="application/vnd.apple.mpegurl")
    if cun is None:
        resp.set_cookie('username', "app1e_s")
    return resp


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
