import atexit
import logging
import os
import sys
from persistence.ImageStore import ImageStore
from flask import Flask, make_response, jsonify, abort
from flask_cors import CORS
from flask_oidc import OpenIDConnect
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

app.config.update({
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_OPENID_REALM': 'how2die',
    'OIDC_INTROSPECTION_AUTH_METHOD': 'bearer',
    'OIDC-SCOPES': ['chan']
})
app.secret_key = "123"

oidc = OpenIDConnect(app)

@app.route('/api/changrid/images/<comment_id>', methods=['GET'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def get_chan_image(comment_id):
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


@app.route('/api/changrid/thumbs/<position>', methods=['GET'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def get_chan_thumbnail(position):
    thumbnail = controller.get_chan_thumbnail(position)
    return {
        "image": thumbnail["image"],
        "commentId": thumbnail["comment_id"],
        "toDelete": "1" if thumbnail["deleted"] else "0"
    }


@app.route('/api/blacklist/<comment_id>', methods=['POST'])
def add_to_blacklist(comment_id):
    controller.add_to_blacklist(comment_id)
    return make_response(jsonify(), 201)


@app.route('/api/favorites/<comment_id>', methods=['POST'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def add_to_favorites(comment_id):
    # TODO: Get actual user id
    success = controller.add_to_favorites(comment_id, 123456)
    if success:
        return make_response(jsonify(), 201)
    else:
        abort(404)


@app.route('/api/favorites/thumbs', methods=['GET'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def get_favorites_thumbnails():
    favorites = controller.get_favorites_thumbnails()
    response_list = list(map(lambda f: {
        "commentId": f["comment_id"],
        "image": f["image"]
    }, favorites))
    return jsonify(response_list)


@app.route('/api/favorites/images/<comment_id>', methods=['GET'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def get_favorite_image(comment_id):
    favorite_image = controller.get_favorite_image(comment_id)
    if favorite_image is None:
        abort(404)
    else:
        return {
            "image": favorite_image["image"],
            "filename": favorite_image["filename"]
        }


@app.route('/api/favorites/images/<comment_id>', methods=['DELETE'])
@oidc.accept_token(require_token=True, scopes_required=['chan'])
def delete_favorite_image(comment_id):
    controller.delete_favorite_image(comment_id)
    return make_response(jsonify(), 204)


if __name__ == '__main__':
    atexit.register(db.close)
    atexit.register(stop_event.set)
    app.run()
