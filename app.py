import json

import requests
from flask import Flask, redirect
from config import BASE64_ENCODED_STRING

app = Flask(__name__)

BASE_URL = "https://apiv2.twitcasting.tv"
SEARCH_URL = BASE_URL + "/search/lives"

HEADER = {"X-Api-Version": "2.0", "Authorization": "Basic %s" % BASE64_ENCODED_STRING.decode("utf-8")}


def get_hls_url(sub_categorie):
    # TwitCastingのSearch APIを叩く
    res = requests.get(SEARCH_URL+"?limit=25&type=category&context=%s&lang=ja" % sub_categorie, headers=HEADER)
    if res.status_code != 200:
        return res.content
    # 結果からmovieオブジェクトのlistを取り出す
    movies = json.loads(res.text)['movies']
    # 最もトータルの視聴者数の多い配信を選択
    best_movie = sorted(movies, reverse=True, key=lambda m: m['movie']['total_view_count'])[0]
    return best_movie['movie']['hls_url']


@app.route('/')
def index():
    return "Hello World"


@app.route('/api')
def tc2vrc_api():
    url = get_hls_url(sub_categorie="music_recite_girls_jp")
    return redirect(url)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
