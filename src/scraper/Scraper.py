from datetime import datetime
from logging import debug
import logging
from model.ImagePost import ImagePost
from model.scoring import compute_score
from model.scoring import get_time_penalty
from persistence.Database import Database
from persistence.ImageStore import ImageStore
from scraper.integration import get_all_ylyl_image_posts, FILE_BASE_URL

NUMBER_OF_WINNERS = 9


class Scraper:
    def __init__(self, db: Database, dl_folder: ImageStore):
        self.db = db
        self.dl_folder = dl_folder

    def main(self):
        db = self.db
        blacklist = db.get_blacklist()
        posts = get_all_ylyl_image_posts()
        clean_blacklist(db, blacklist, posts.keys())
        existing_winners = db.get_grid_items()
        refreshed_winners = refresh_winners(existing_winners, posts)
        new_winners = update_winners(posts.values(), refreshed_winners, blacklist)
        clean_download_folder(self.dl_folder, new_winners)
        download_files(self.dl_folder, new_winners, blacklist)
        db.save_grid_items(new_winners)
        print_status(new_winners)


def refresh_winners(existing_winners: list[ImagePost], posts: dict[int, ImagePost]):
    return [refresh(winner, posts) for winner in existing_winners]


def refresh(winner, posts):
    return posts[winner.id] if winner.id in posts else winner


def get_top_candidates(n, posts: list[ImagePost]) -> list[tuple[ImagePost, int]]:
    posts_with_scores = [(post, compute_score(post)) for post in posts]
    top = sorted(posts_with_scores, key=lambda post: post[1], reverse=True)
    top = top[:n]
    top.reverse()
    return top


def clean_blacklist(db: Database, blacklist: list[int], posts: list[int]):
    timed_out = [p for p in blacklist if p not in posts]
    for p in timed_out:
        db.remove_from_blacklist(p)


def update_winners(posts: list[ImagePost], winners: list[ImagePost], blacklist: list[int]) -> list[ImagePost]:
    to_exclude = blacklist + [post.id for post in winners]
    filtered_posts = list(filter(lambda post: post.id not in to_exclude, posts))
    candidates = get_top_candidates(NUMBER_OF_WINNERS, filtered_posts)
    current_winners = [(post, compute_score(post)) for post in winners]
    current_winners = [(post, -1000000 if post.id in blacklist else score)for post, score in current_winners]
    for candidate, score in candidates:
        position, existing_score = lowest_score(current_winners)
        if score > existing_score:
            current_winners[position] = (candidate, score)
    return [winner[0] for winner in current_winners]


def lowest_score(posts: list[tuple[ImagePost, int]]):
    lowest = (0, 1000000)
    for position in range(0, len(posts)):
        score = posts[position][1]
        if score < lowest[1]:
            lowest = (position, score)
    return lowest[0], lowest[1]


def download_files(dl_folder: ImageStore, winners: list[ImagePost], blacklist: list[int]):
    for post in winners:
        if post.id not in blacklist:
            try:
                dl_folder.download_file(FILE_BASE_URL + post.image, post.image)
                dl_folder.download_file(FILE_BASE_URL + post.thumb, post.thumb)
            except Exception as e:
                print("Failed to download files: " + str(e.reason))
                return


def clean_download_folder(dl_folder: ImageStore, winners: list[ImagePost]):
    to_keep = [post.image for post in winners] + [post.thumb for post in winners]
    dl_folder.clean(to_keep)


def print_status(winners: list[ImagePost]):
    debug("Status:")
    for position in range(0, len(winners)):
        winner = winners[position]
        debug("Position " + str(position) +
              " --- id: " + str(winner.id) +
              ", score: " + str(compute_score(winner)) +
              ", last seen: " + str(round(datetime.now().timestamp() - winner.last_seen.timestamp())) + "s ago" +
              ", time penalty: " + str(get_time_penalty(winner)))
