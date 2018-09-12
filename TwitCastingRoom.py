# -*- coding: utf-8 -*-
from datetime import datetime
from flask import Flask, request, redirect, render_template, Response
from werkzeug.contrib.cache import SimpleCache
import requests
import json

from config import BASE64_ENCODED_STRING

app = Flask(__name__)
cache = SimpleCache()


BASE_URL = "https://apiv2.twitcasting.tv"
MOVIE_URL = BASE_URL + "/movies/{movie_id}"
USER_URL = BASE_URL + "/users/{user_id}"
SEARCH_URL = BASE_URL + "/search/lives"


HEADER = {"X-Api-Version": "2.0", "Authorization": "Basic %s" % BASE64_ENCODED_STRING.decode("utf-8")}


def get_recommend():
    rv = cache.get('data')
    if rv is None:
        res = requests.get(SEARCH_URL+"?limit=6&type=recommend&lang=ja", headers=HEADER)
        if res.status_code != 200:
            return "通信エラー"
        rv = json.loads(res.text)
        cache.set('data', rv, timeout=1 * 60)
    return rv


def get_user(screen_id):
    res = requests.get(USER_URL.format(user_id=screen_id), headers=HEADER)
    if res.status_code == 200:
        return json.loads(res.text)
    return {"error": {"message": "status error"}}


def is_user_living(user):
    return user["user"]["is_live"]


def is_movie_living(movie):
    return movie["movie"]["is_live"]


def last_movie_hls_url(user):
    last_movie_id = user["user"]["last_movie_id"]
    res = requests.get(MOVIE_URL.format(movie_id=last_movie_id))
    if res.status_code == 200:
        return json.loads(res.text)["movie"]["hls_url"]


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
    if n == 6:
        return "6"
    data = get_recommend()
    return redirect(data["movies"][n-1]["movie"]["hls_url"])


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

