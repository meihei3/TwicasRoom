# -*- coding: utf-8 -*-

from flask import Flask, request, redirect
import requests
import json

from config import BASE64_ENCODED_STRING

app = Flask(__name__)


BASE_URL = "https://apiv2.twitcasting.tv"
OAUTH2_URL = BASE_URL + "/oauth2"
CATEGORY_URL = BASE_URL + "/categories"
COMMENT_URL = BASE_URL + "/movies/{movie_id}/comments"
USER_URL = BASE_URL + "/users/{user_id}"
SEARCH_URL = BASE_URL + "/search/lives"


HEADER = {"X-Api-Version": "2.0", "Authorization": "Basic %s" % BASE64_ENCODED_STRING.decode("utf-8")}


def get_recommend():
    res = requests.get(SEARCH_URL+"?limit=5&type=recommend&lang=ja", headers=HEADER)
    if res.status_code == 200:
        return json.loads(res.text)
    return "通信エラー"


@app.route('/')
def hello_world():
    return 'Hello World!'


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


if __name__ == '__main__':
    app.run()

