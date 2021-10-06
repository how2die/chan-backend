from threading import Thread
from scraper.Scraper import Scraper

SLEEP_TIME = 60

class ScraperThread(Thread):
	def __init__(self, event, scraper : Scraper):
		Thread.__init__(self)
		self.stopped = event
		self.scraper = scraper

	def run(self):
		self.scraper.main()
		while not self.stopped.wait(SLEEP_TIME):
			try:
				self.scraper.main()
			except Exception as e:
				print("An error ocurred: ", repr(e))
