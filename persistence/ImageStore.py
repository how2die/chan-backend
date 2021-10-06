import base64
import os
from logging import debug
from shutil import copy2
import urllib

class ImageStore:

	def __init__(self, folder : str):
		self.folder = folder
		if not os.path.exists(folder):
			os.makedirs(folder)

	def filepath(self, filename):
		return os.path.join(self.folder, filename)

	def download_file(self, url, filename):
		filepath = self.filepath(filename)
		if not os.path.isfile(filepath):
			debug("Downloading " + url)
			urllib.request.urlretrieve(url, filepath)

	def get_image(self, filename):
		filepath = self.filepath(filename)
		if not os.path.exists(filepath):
			return None
		with open(filepath, "rb") as image_file:
			image_encoded = base64.b64encode(image_file.read())
			return image_encoded.decode('ascii')

	def delete(self, filename):
		filepath = self.filepath(filename)
		if os.path.exists(filepath):
			os.remove(filepath)

	def clean(self, files_to_keep):
		for file in os.listdir(self.folder):
			if file not in files_to_keep:
				filepath = self.filepath(file)
				os.remove(filepath)

	def copy_from(self, other_image_store, filename):
		src = other_image_store.filepath(filename)
		dst = self.folder
		copy2(src, dst)
			