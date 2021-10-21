import atexit
import json
import jwt
import logging
import os
import requests
import sys

from persistence.ImageStore import ImageStore
from flask import Flask, request, make_response, jsonify, abort
from flask_cors import CORS
from controller.Controller import Controller
from persistence.Database import Database
from scraper.Scraper import Scraper
from scraper.ScraperThread import ScraperThread
from threading import Event

DL_FOLDER = os.getenv("DL_FOLDER", "/var/chan/downloads/")
FAVS_FOLDER = os.getenv("FAVS_FOLDER", "/var/chan/favorites/")
DB_CONFIG = { 
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "chan"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres")
}

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
app = Flask(__name__)
cors = CORS(app)
db = Database(DB_CONFIG)
dl_folder = ImageStore(DL_FOLDER)
favs_folder = ImageStore(FAVS_FOLDER)
controller = Controller(db, dl_folder, favs_folder)
scraper = Scraper(db, dl_folder)
stop_event = Event()
scraper_daemon = ScraperThread(stop_event, scraper)
scraper_daemon.daemon = True
scraper_daemon.start()

def _load_public_key():
    response = requests.get('https://auth.how2die.com/auth/realms/how2die/')
    json_response = json.loads(response.content)
    return json_response["public_key"]

PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\n" + _load_public_key() + "\n-----END PUBLIC KEY-----"

def _authorize(headers):
    global PUBLIC_KEY
    if "Authorization" not in headers:
        abort(401)

    authorization_header = headers["Authorization"]
    if not authorization_header.startswith("Bearer "):
        abort(401)
    
    token = authorization_header[7:]
    decoded_token = jwt.decode(token, PUBLIC_KEY, audience="account", algorithms=['RS256'])
    if not "chan" in decoded_token["realm_access"]["roles"]:
        abort(403)

@app.route('/chan/api/changrid/images/<comment_id>', methods=['GET'])
def get_chan_image(comment_id):
    _authorize(request.headers)
    image = controller.get_chan_image(comment_id)
    if image is None:
        abort(404)
    else:
        return {
            "image": image["image"],
            "filename": image["filename"],
            "liked": image["liked"],
            "summary": image["summary"]
        }


@app.route('/chan/api/changrid/thumbs/<position>', methods=['GET'])
def get_chan_thumbnail(position):
    _authorize(request.headers)
    thumbnail = controller.get_chan_thumbnail(position)
    return {
        "image": thumbnail["image"],
        "commentId": thumbnail["comment_id"],
        "toDelete": "1" if thumbnail["deleted"] else "0"
    }


@app.route('/chan/api/blacklist/<comment_id>', methods=['POST'])
def add_to_blacklist(comment_id):
    controller.add_to_blacklist(comment_id)
    return make_response(jsonify(), 201)


@app.route('/chan/api/favorites/<comment_id>', methods=['POST'])
def add_to_favorites(comment_id):
    _authorize(request.headers)
    # TODO: Get actual user id
    success = controller.add_to_favorites(comment_id, 123456)
    if success:
        return make_response(jsonify(), 201)
    else:
        abort(404)


@app.route('/chan/api/favorites/thumbs', methods=['GET'])
def get_favorites_thumbnails():
    _authorize(request.headers)
    favorites = controller.get_favorites_thumbnails()
    response_list = list(map(lambda f: {
        "commentId": f["comment_id"],
        "image": f["image"]
    }, favorites))
    return jsonify(response_list)


@app.route('/chan/api/favorites/images/<comment_id>', methods=['GET'])
def get_favorite_image(comment_id):
    _authorize(request.headers)
    favorite_image = controller.get_favorite_image(comment_id)
    if favorite_image is None:
        abort(404)
    else:
        return {
            "image": favorite_image["image"],
            "filename": favorite_image["filename"]
        }


@app.route('/chan/api/favorites/images/<comment_id>', methods=['DELETE'])
def delete_favorite_image(comment_id):
    _authorize(request.headers)
    controller.delete_favorite_image(comment_id)
    return make_response(jsonify(), 204)


if __name__ == '__main__':
    atexit.register(db.close)
    atexit.register(stop_event.set)
    app.run()
