import datetime


class ImagePost:
    def __init__(self, id: int, image: str, thumb: str, last_seen: datetime, summary: str):
        self.id = id
        self.image = image
        self.thumb = thumb
        self.summary = summary
        self.last_seen = last_seen

    def comments(self):
        if not 'replies' in self.summary:
            return []
        return [reply['com'] if 'com' in reply else "" for reply in self.summary['replies']]
