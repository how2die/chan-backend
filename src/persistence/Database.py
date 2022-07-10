from logging import debug
from model.ImagePost import ImagePost
import json
import psycopg2
from tenacity import retry, wait_exponential, stop_after_attempt
from typing import Callable


def reconnect(f: Callable):
    def wrapper(db, *args, **kwargs):
        if not db.connected():
            db.connect()
        try:
            return f(db, *args, **kwargs)
        except psycopg2.Error:
            db.close()
            raise
    return wrapper


class Database:

    def __init__(self, config):
        self._config = config
        self._connection = None

    def connected(self) -> bool:
        return self._connection and self._connection.closed == 0

    def connect(self):
        self.close()
        debug('Connecting to the PostgreSQL database...')
        self._connection = psycopg2.connect(**self._config)

    def close(self):
        if self.connected():
            try:
                self._connection.close()
            except Exception:
                pass
        self._connection = None

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_grid_items(self) -> list[ImagePost]:
        query = "SELECT position, commentid, image, thumb, last_seen, summary FROM changrid ORDER BY position ASC;"
        cursor = self._connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        dictionary = [ImagePost(e[1], e[2], e[3], e[4], json.loads(e[5])) for e in result]
        return dictionary

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def save_grid_items(self, winners : list[ImagePost]):
        position = 0
        for post in winners:
            query = """UPDATE changrid 
            SET image = %(image)s, thumb = %(thumb)s, commentid = %(comment_id)s, 
            summary = %(summary)s, last_seen = %(last_seen)s
            WHERE position = %(index)s;"""
            data = {
                "image": post.image,
                "thumb": post.thumb,
                "comment_id": post.id,
                "summary": json.dumps(post.summary),
                "index": position,
                "last_seen": post.last_seen
            }
            cursor = self._connection.cursor()
            cursor.execute(query, data)
            self._connection.commit()
            cursor.close()
            position = position + 1

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_grid_item(self, position):
        query = "SELECT image, thumb, commentid, summary FROM changrid WHERE position = %(position)s;"
        data = {"position": position}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        position = cursor.fetchall()[0]
        cursor.close()
        return position

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_grid_item_for_comment(self, comment_id):
        query = """SELECT image, thumb, commentid, summary, 
        (SELECT COUNT(*) FROM chanfavs WHERE chanfavs.commentid = %(comment_id)s)
        FROM changrid
        WHERE commentid = %(comment_id)s;"""
        data = {"comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        result = cursor.fetchall()
        if not result:
            cursor.close()
            return None
        else:
            grid_item = result[0]
            cursor.close()
            return grid_item

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def save_to_favorites(self, comment_id, user_id):
        query = """INSERT INTO chanfavs (commentid, image, thumb, summary, userid, time)
        SELECT commentid, image, thumb, summary, %(user_id)s, NOW() FROM changrid WHERE commentid = %(comment_id)s;"""
        data = {"user_id": user_id, "comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        self._connection.commit()
        cursor.close()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_favorites(self):
        query = "SELECT commentid, thumb FROM chanfavs ORDER BY commentid DESC;"
        cursor = self._connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_favorite(self, comment_id):
        query = """SELECT image, thumb, commentid, summary 
        FROM chanfavs
        WHERE commentid = %(comment_id)s;"""
        data = {"comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        result = cursor.fetchall()
        if not result:
            cursor.close()
            return None
        else:
            grid_item = result[0]
            cursor.close()
            return grid_item

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def delete_favorite(self, comment_id):
        query = "DELETE FROM chanfavs WHERE commentid = %(comment_id)s;"
        data = {"comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        self._connection.commit()
        cursor.close()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def add_to_blacklist(self, comment_id):
        query = "INSERT INTO blacklist (comment_id) VALUES (%(comment_id)s);"
        data = {"comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        self._connection.commit()
        cursor.close()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def remove_from_blacklist(self, comment_id):
        query = "DELETE FROM blacklist WHERE comment_id = %(comment_id)s;"
        data = {"comment_id": comment_id}
        cursor = self._connection.cursor()
        cursor.execute(query, data)
        self._connection.commit()
        cursor.close()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential())
    @reconnect
    def get_blacklist(self):
        query = "SELECT comment_id FROM blacklist;"
        cursor = self._connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return [e[0] for e in result]
