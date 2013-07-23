import time, sys, os, re, random
import string, cgi, time, math
from urlparse import urlparse
import urllib2
from threading import Thread
import shutil
from t0mm0.common.addon import Addon
from threadpool import *
import xbmc
import xbmcaddon
import hashlib
#from proxy import *

ADDON_ID = 'script.module.walter'
SELF = xbmcaddon.Addon(id=ADDON_ID)
ROOT_PATH = SELF.getAddonInfo('path')
sys.path.append( os.path.join( ROOT_PATH, 'lib', 'walter' ) )

from donnie.settings import Settings
reg = Settings(['plugin.video.theroyalwe', 'script.module.walter'])

from databaseconnector import DatabaseClass
from caching import CachingClass

try: 
	import simplejson as json
                                                                                                                                                                                                                                                        
except ImportError: 
	import json  
table = [10,20,30,45,60]
POLLING_DELAY = table[int(reg.getSetting('polling-delay'))]

class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Walter:
	def __init__(self):
		global ADDON_ID
		global reg
		ADDON = Addon(ADDON_ID)
		self.data_root = ADDON.get_profile()
		if reg.getBoolSetting('cache_temp_custom_directory'):
			self.cache_root = reg.getSetting('cache_temp_directory')
		else:
			self.cache_root = os.path.join(xbmc.translatePath(self.data_root + 'cache'), '')
		print "Setting cache_root: %s" % self.cache_root
		self.mkdir(self.cache_root)

		if reg.getBoolSetting('cache_movie_custom_directory'):
			self.movie_root = reg.getSetting('cache_movie_directory')
		else:
			self.movie_root = os.path.join(xbmc.translatePath(self.data_root + 'cache/movies'), '')
		print "Setting movie_root: %s" % self.movie_root
		self.mkdir(self.movie_root)

		if reg.getBoolSetting('cache_tvshow_custom_directory'):
			self.tvshow_root = reg.getSetting('cache_tvshow_directory')
		else:
			self.tvshow_root = os.path.join(xbmc.translatePath(self.data_root + 'cache/tvshows'), '')	
		print "Setting tvshow_root: %s" % self.tvshow_root
		self.mkdir(self.tvshow_root)

		db_file = os.path.join(xbmc.translatePath(self.data_root), 'walter.db')
		sql_path = os.path.join(xbmc.translatePath(ROOT_PATH + '/resources/database'), '')
		self.DB = DatabaseClass(db_file, sql_path)

	def notify(self, title, message, image=''):
		xbmc.executebuiltin("XBMC.Notification("+title+","+message+", 1000, "+image+")")

	def mkdir(self, dir_path):
		dir_path = dir_path.strip()
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)

if __name__ == '__main__':
	filename = None
	Wt = Walter()
	xbmc.log("Walter Caching Service starting...")
	xbmc.log("Marking abandoned jobs as failed.")
	Wt.DB.execute("UPDATE wt_download_queue SET status=3 WHERE status=1")
	Wt.DB.commit()
	while(not xbmc.abortRequested):
		if not reg.getBoolSetting('enable-caching'):
			print "Caching service disabled in settings, enable and restart to proceed."
			break
		row = Wt.DB.query("SELECT * FROM wt_download_queue WHERE status=0 ORDER BY num ASC LIMIT 1")
		if row:
			Ca = CachingClass(Wt.cache_root, Wt.DB)
			try:
				filename = Ca.Cache(row[0], row[2], row[3], media=row[1], folder=row[5])
			except Exception, e:
				Ca = CachingClass(Wt.cache_root, Wt.DB)
				filename = None

			if filename:
				Wt.notify('Cache Complete', filename)
			else:
				Wt.notify('Caching Error', 'Check the log for details.')
			filename = None

		xbmc.sleep(POLLING_DELAY * 1000)
	#Wp = None
	Wt = None
	xbmc.log("Walter Caching Service stopping...")
