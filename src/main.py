import atexit
import json
import logging
import jwt
import requests
import sys
import settings

from persistence.ImageStore import ImageStore
from fastapi import Depends, FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OpenIdConnect
from fastapi.openapi.utils import get_openapi
from controller.Controller import Controller
from persistence.Database import Database
from pydantic import BaseModel
from pydantic.schema import Optional
from scraper.Scraper import Scraper
from scraper.ScraperThread import ScraperThread
from threading import Event
from typing import List

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

oidc = OpenIdConnect(openIdConnectUrl=f'{settings.auth_host}/auth/realms/how2die/.well-known/openid-configuration')

app = FastAPI(swagger_ui_init_oauth={"clientId": "chan",
                                     "appName": "Chan backend",
                                     "scopes": "openid profile", })
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = Database({
    "host": settings.db_host,
    "port": settings.db_port,
    "database": settings.db_name,
    "user": settings.db_username,
    "password": settings.db_password
})
dl_folder = ImageStore(settings.download_folder)
favs_folder = ImageStore(settings.favorites_folder)
controller = Controller(db, dl_folder, favs_folder)
scraper = Scraper(db, dl_folder)
stop_event = Event()
scraper_daemon = ScraperThread(stop_event, scraper)
scraper_daemon.daemon = True
scraper_daemon.start()


class Thumbnail(BaseModel):
    commentId: int
    image: str
    toDelete: Optional[bool]


class ImagePost(BaseModel):
    commentId: int
    image: str
    filename: str
    liked: bool
    summary: str


def _load_public_key():
    response = requests.get(f'{settings.auth_host}/auth/realms/how2die/')
    json_response = json.loads(response.content)
    return json_response["public_key"]


PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\n" + \
    _load_public_key() + "\n-----END PUBLIC KEY-----"


def _authorize(headers):
    global PUBLIC_KEY
    if "Authorization" not in headers:
        raise HTTPException(status_code=401)

    authorization_header = headers["Authorization"]
    if not authorization_header.startswith("Bearer "):
        raise HTTPException(status_code=401)

    token = authorization_header[7:]
    decoded_token = jwt.decode(
        token, PUBLIC_KEY, audience="account", algorithms=['RS256'])
    if not "chan" in decoded_token["realm_access"]["roles"]:
        raise HTTPException(status_code=403)


# TODO: Decide whether this is worse/better than _authorize()
def _authorize2(bearer_token: str):
    global PUBLIC_KEY
    if not bearer_token.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = bearer_token[7:]
    decoded_token = jwt.decode(
        token, PUBLIC_KEY, audience="account", algorithms=['RS256'])
    if not "chan" in decoded_token["realm_access"]["roles"]:
        raise HTTPException(status_code=403)


@app.get('/chan/api/changrid/images/{comment_id}', response_model=ImagePost, tags=["changrid"])
async def get_chan_image(comment_id: int, token=Depends(oidc)):
    """Get a specific image with associated comment data.
    """
    _authorize2(token)
    image = controller.get_chan_image(comment_id)
    if image is None:
        raise HTTPException(status_code=404)
    else:
        response = {
            "commentId": comment_id,
            "image": image["image"],
            "filename": image["filename"],
            "liked": image["liked"],
            "summary": image["summary"]
        }
        return response


@app.get('/chan/api/changrid/thumbs/{position}', response_model=Thumbnail, tags=["changrid"])
async def get_chan_thumbnail(request: Request, position: int):
    """Get the thumbnail and data for a given position in the grid.
    """
    _authorize(request.headers)
    thumbnail = controller.get_chan_thumbnail(position)
    response = {
        "image": thumbnail["image"],
        "commentId": thumbnail["comment_id"],
        "toDelete": thumbnail["deleted"]
    }
    return response


@app.post('/chan/api/blacklist/{comment_id}', status_code=201, response_class=Response, tags=["changrid"])
async def add_to_blacklist(comment_id: int):
    controller.add_to_blacklist(comment_id)


@app.post('/chan/api/favorites/{comment_id}', status_code=201, response_class=Response, tags=["chanfavorites"])
async def add_to_favorites(request: Request, comment_id: int):
    _authorize(request.headers)
    # TODO: Get actual user id
    success = controller.add_to_favorites(comment_id, 123456)
    if not success:
        raise HTTPException(status_code=404)


@app.get('/chan/api/favorites/thumbs', response_model=List[Thumbnail], tags=["chanfavorites"])
async def get_favorites_thumbnails(request: Request):
    _authorize(request.headers)
    favorites = controller.get_favorites_thumbnails()
    response_list = list(map(lambda f: {
        "commentId": f["comment_id"],
        "image": f["image"]
    }, favorites))
    return response_list


@app.get('/chan/api/favorites/images/{comment_id}', response_model=ImagePost, tags=["chanfavorites"])
async def get_favorite_image(request: Request, comment_id: int):
    _authorize(request.headers)
    favorite_image = controller.get_favorite_image(comment_id)
    if favorite_image is None:
        raise HTTPException(status_code=404)
    else:
        response = {
            "commentId": comment_id,
            "image": favorite_image["image"],
            "filename": favorite_image["filename"],
            "summary": favorite_image["summary"],
            "liked": True
        }
        return response


@app.delete('/chan/api/favorites/{comment_id}', status_code=204, response_class=Response, tags=["chanfavorites"])
async def delete_from_favorites(request: Request, comment_id: int):
    _authorize(request.headers)
    controller.delete_favorite_image(comment_id)

def _custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Chan backend",
        version="1.0.0",
        description="Where the magix happen",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

atexit.register(db.close)
atexit.register(stop_event.set)
app.openapi = _custom_openapi
