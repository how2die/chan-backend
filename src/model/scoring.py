from datetime import datetime
from model.ImagePost import ImagePost


def compute_score(post: ImagePost) -> int:
    total = 1
    for comment in post.comments():
        comment_lower = comment.lower()
        total += 4  # 4 points for being referenced
        for word, value in _word_values().items():
            if word in comment_lower:
                total += value
    return total - get_time_penalty(post)


def get_time_penalty(post: ImagePost):
    # Penalty: 1 point per 3 minutes after 404
    return round((datetime.now().timestamp() - post.last_seen.timestamp()) / 180)


def _word_values() -> dict[str, int]:
    return {
        'lost': 30,
        'lose': 20,
        'lol': 10,
        'rofl': 10,
        'every': 20,
        'time': 20,
        'laugh': 20,
        'haha': 15,
        'kek': 15,
        'sides': 20,
        'report': -100,
        'sick': -35,
        'disgust': -60,
        'mods': -100
    }
