from persistence.ImageStore import ImageStore
from persistence.Database import Database


class Controller:
    def __init__(self, db: Database, dl_folder: ImageStore, favs_folder: ImageStore):
        self.db = db
        self.dl_folder = dl_folder
        self.favs_folder = favs_folder

    def get_chan_image(self, comment_id):
        blacklist = self.db.get_blacklist()
        if int(comment_id) in blacklist:
            return None
        grid_item = self.db.get_grid_item_for_comment(comment_id)
        if grid_item is None:
            return None
        filename = grid_item[0]
        summary = grid_item[3]
        liked = grid_item[4] == 1
        encoded_image = self.dl_folder.get_image(filename)
        if encoded_image is None:
            return None
        return {"image": encoded_image, "filename": filename, "liked": liked, "summary": summary}

    def get_chan_thumbnail(self, position):
        grid_item = self.db.get_grid_item(position)
        blacklist = self.db.get_blacklist()
        filename = grid_item[1]
        comment_id = grid_item[2]
        deleted = True if comment_id in blacklist else False
        encoded_image = self.dl_folder.get_image(filename)
        img_string = encoded_image if encoded_image is not None else ""
        return {"image": img_string, "comment_id": comment_id, "deleted": deleted}

    def add_to_blacklist(self, comment_id):
        self.db.add_to_blacklist(comment_id)
        grid_item = self.db.get_grid_item_for_comment(comment_id)
        if grid_item is not None:
            thumb = grid_item[0]
            image = grid_item[1]
            self.dl_folder.delete(image)
            self.dl_folder.delete(thumb)

    def add_to_favorites(self, comment_id, user_id):
        existing = self.db.get_favorite(comment_id)
        if existing is not None:
            return True
        grid_item = self.db.get_grid_item_for_comment(comment_id)
        if grid_item is not None:
            thumb = grid_item[0]
            image = grid_item[1]
            self.favs_folder.copy_from(self.dl_folder, thumb)
            self.favs_folder.copy_from(self.dl_folder, image)
            self.db.save_to_favorites(comment_id, user_id)
            return True
        else:
            return False

    def get_favorites_thumbnails(self):
        favorites = self.db.get_favorites()
        return list(map(lambda f: {
            "comment_id": f[0],
            "image": self.favs_folder.get_image(f[1])
        }, favorites))

    def get_favorite_image(self, comment_id):
        grid_item = self.db.get_favorite(comment_id)
        if grid_item is None:
            return None
        filename = grid_item[0]
        summary = grid_item[3]
        encoded_image = self.favs_folder.get_image(filename)
        if encoded_image is None:
            return None
        return {"image": encoded_image, "filename": filename, "summary": summary}

    def delete_favorite_image(self, comment_id):
        grid_item = self.db.get_favorite(comment_id)
        if grid_item is not None:
            thumb = grid_item[0]
            image = grid_item[1]
            self.favs_folder.delete(image)
            self.favs_folder.delete(thumb)
            self.db.delete_favorite(comment_id)
