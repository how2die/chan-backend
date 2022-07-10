from datetime import datetime
from model.ImagePost import ImagePost
import logging
import re
import requests

CATALOG_BASE_URL = "http://a.4cdn.org/b/catalog.json"
THREAD_URL_TEMPLATE = "http://a.4cdn.org/b/thread/thread_id.json"
FILE_BASE_URL = "http://i.4cdn.org/b/"


def get_all_ylyl_image_posts() -> dict[int, ImagePost]:
	posts = get_all_ylyl_posts()
	result = {}
	(replies, references) = extract_replies(posts)
	for _, post in posts.items():
		if 'filename' in post:
			id = post['no']
			image = str(post['tim']) + post['ext']
			thumb = str(post['tim']) + "s.jpg"
			last_seen = datetime.now()
			summary = create_summary(post, posts, replies, references)
			result[id] = ImagePost(id, image, thumb, last_seen, summary)
	return result


def extract_replies(posts):
	replies = {}
	references = {}
	for id, post in posts.items():
		replies[id] = []
		references[id] = []

	pattern = re.compile(r"\"#p(\d*)\"")  # e.g. "#p757839917"
	for post_id, post in posts.items():
		if 'com' in post:
			reference_ids = pattern.findall(post['com'])
			for reference_id in reference_ids:
				if int(reference_id) in posts:
					references[post_id].append(int(reference_id))
					replies[int(reference_id)].append(post_id)
	return (replies, references)


def create_summary(post, posts, replies, references):
	summary = {}
	summary['post'] = post
	summary['op'] = posts[post['resto']] if post['resto'] in posts else post
	referenced_posts = []
	for reference_id in references[post['no']]:
		if reference_id in posts:
			referenced_posts.append(posts[reference_id])
	summary['references'] = referenced_posts
	replied_posts = []
	for reply_id in replies[post['no']]:
		if reply_id in posts:
			replied_posts.append(posts[reply_id])
	summary['replies'] = replied_posts
	return summary


# Return dictionary of posts (id -> post)
def get_all_ylyl_posts():
	ylyl_posts = {}
	for thread_id in get_ylyl_threads():
		for post in get_posts(thread_id):
			ylyl_posts[post['no']] = post
	return ylyl_posts

# Return dictionary of threads {id -> comment}


def get_threads():
	threads = {}
	try:
		r = requests.get(CATALOG_BASE_URL)
		catalog = r.json()
		for page in catalog:
			for thread in page.get('threads'):
				id = thread['no']
				comment = thread.get('com', "")
				threads[id] = comment
	except requests.exceptions.RequestException as e:
		logging.error("Error retrieving catalog")
		logging.error(e)
	except ValueError:
		logging.error("Error parsing catalog as JSON")
	return threads

def get_ylyl_threads() -> list[int]:
	ylyl_threads = []
	all_threads = get_threads()
	for id, comment in all_threads.items():
		lower = comment.lower()
		if 'ylyl' in lower \
				or 'laugh' in lower \
				or 'lose' in lower \
				or 'raff' in lower \
				or 'ruse' in lower:
			ylyl_threads.append(id)
	return ylyl_threads

# Return dictionary of posts (id -> post)
#
# Example post: {
# 	no		757847553
# 	now		"01/24/18(Wed)12:26:03"
# 	name	"Anonymous"
# 	com		"<a href=\"#p757841044\" class=\"quotelink\">&gt;&gt;757841044</a>"
# 	filename"5wugn7qebdvz"
# 	ext		".jpg"
# 	w		975
# 	h		689
# 	tn_w	124
# 	tn_h	88
# 	tim		1516814763897
# 	time	1516814763
# 	md5		"eoHBP98QakQ/L/oJRqG7eQ=="
# 	fsize	272792
# 	resto	757839802
# }


def get_posts(thread_id):
	try:
		thread_url = THREAD_URL_TEMPLATE.replace("thread_id", str(thread_id))
		r = requests.get(thread_url)
		thread = r.json()
		return thread.get('posts')
	except requests.exceptions.RequestException as e:
		logging.error("Error retrieving thread")
		logging.error(e)
	except ValueError:
		logging.error("Error parsing JSON for thread: " + str(thread_id))
	return []
