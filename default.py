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

ADDON_ID = 'script.module.walter'
SELF = xbmcaddon.Addon(id=ADDON_ID)
ROOT_PATH = SELF.getAddonInfo('path')
sys.path.append( os.path.join( ROOT_PATH, 'resources', 'lib' ) )

from databaseconnector import DatabaseClass

try: 
	import simplejson as json
                                                                                                                                                                                                                                                        
except ImportError: 
	import json  


class Walter:
	def __init__(self):
		global ADDON_ID
		ADDON = Addon(ADDON_ID)
		self.data_root = ADDON.get_profile()
		self.cache_root = os.path.join(xbmc.translatePath(self.data_root + 'cache'), '')
		db_file = os.path.join(xbmc.translatePath(self.data_root), 'walter.db')
		sql_path = os.path.join(xbmc.translatePath(ROOT_PATH + '/resources/database'), '')
		self.DB = DatabaseClass(db_file, sql_path)




if __name__ == '__main__':
	Wt = Walter()
	xbmc.log("Walter Caching Service starting...")
	while(not xbmc.abortRequested):
		xbmc.sleep(1000)
	xbmc.log("Walter Caching Service stopping...")
