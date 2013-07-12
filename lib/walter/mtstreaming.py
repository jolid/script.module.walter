import urllib2, re, os, math, sys
import xbmc, xbmcaddon, xbmcgui,xbmcplugin
import random, time
import htmlcleaner
from threading import Thread
import shutil
from t0mm0.common.addon import Addon
from threadpool import *

#from databaseconnector import DatabaseClass
addon = Addon('script.module.walter')
addon_path = addon.get_path()
profile_path = addon.get_profile()

from donnie.settings import Settings
reg = Settings(['script.module.walter'])

class MTStreaming:
	def __init__(self):
		global profile_path
		global reg		
		if reg.getBoolSetting('cache_temp_custom_directory'):
			self.cache_root = reg.getSetting('cache_temp_directory')
		else:
			self.cache_root = os.path.join(xbmc.translatePath(profile_path + 'cache'), '')
		self.pDialog = xbmcgui.DialogProgress()
		self.output_file = ''
		self._cached = 0
		self.total_segments = 0
		self.completed = []
		table = [15,25,35,50,75]
		self.pre_cache_bytes = table[int(reg.getSetting('pre-caching-mb'))] * 1000 * 1000
		self._active_threads = 0
		self.threads = 1 + int(reg.getSetting('max-cache-threads'))
		table = [5,8,10,15,20]
		self.segments = table[int(reg.getSetting('pre-caching-segments'))]
		self.chunk_size = 1 * 1024
		self.segment_size = self.pre_cache_bytes / self.segments
		self.output_file = os.path.join(xbmc.translatePath(self.cache_root), 'mtstrm.avi')
		self.compiler=None

	def getMeta(self):
		self.net = urllib2.urlopen(self.url)
		self.headers = self.net.headers.items()
		self.total_bytes = int(self.net.headers["Content-Length"])
		self.total_segments = int(math.ceil(self.total_bytes / self.segment_size))

	def _download(self, url, p, silent=True):
		start = p * self.segment_size
		end = (start + self.segment_size) - 1
		r = 'bytes=%s-%s' % (start, end)
		while True:
			try:
				req = urllib2.Request(url, headers={"Range" : r})
				f = urllib2.urlopen(req)
				break
			except urllib2.URLError, e:
				xbmc.sleep(5000)
				pass
		self._active_threads = self._active_threads + 1

		print "Requesting: %s" % r
		filename = '%s_mtstrm.part' % str(p).zfill(3)
		path = os.path.join(xbmc.translatePath(self.cache_root), filename)
		req = urllib2.Request(url, headers={"Range" : r})
		f = urllib2.urlopen(req)
		total_mbs = self.pre_cache_bytes / 1000000
		with open(path, 'wb+') as fp:
			while True:
    				buff = f.read(self.chunk_size)
				if not buff: break
				self._cached = self._cached + self.chunk_size
				if not silent:
					percent = self._cached * 100 / self.pre_cache_bytes
					#segs = "%s of %s active threads" % (self._active_threads, self.threads)
					mbs = '%.01f MB of %.01f MB with %s of %s threads' % (self._cached / 1000000, total_mbs, self._active_threads, self.threads)
					self.pDialog.update(percent, mbs, '')
				fp.write(buff)

		return p

	def _completed(self, request, result):
		print "Completed: %s" % result
		self._active_threads = self._active_threads - 1
		self.completed.append(result)

	def _pre_cache(self):
		print "Pre caching initial segments 0-%s" % self.segments
		for p in range(0,self.segments):
			self.Pool.putRequest(WorkRequest(self._download, args=(self.url, p), callback=self._completed))
			try:
			    self.Pool.poll()
			except NoResultsPending:
			    pass
		self.Pool.wait()
		#self.Pool.joinAllDismissedWorkers()
		return

	def _cache(self):
		print "Caching remaing segments %s-%s" % (self.segments+1, self.total_segments)
		for p in range(0, self.total_segments):
			self.Pool.putRequest(WorkRequest(self._download, args=(self.url, p), callback=self._completed))
			try:
			    self.Pool.poll()
			except NoResultsPending:
			    pass
		#self.Pool.wait()
		#self.Pool.joinAllDismissedWorkers()

	def _pre_compile(self):
		print "Waiting to pre-compile segments"
		p=0
		stream = open(self.output_file, 'wb')
		while(p< self.segments):
			if p in self.completed:
				percent = p * 100 / self.segments
				infile = '%s_mtstrm.part' % str(p).zfill(3)
				infile = os.path.join(xbmc.translatePath(self.cache_root), infile)
				shutil.copyfileobj(open(infile, 'rb'), stream) 
				print "compiled %s" % p
				os.remove(infile)
				p = p+1
				status = "%s of %s" % (p, self.segments)
				self.pDialog.update(percent, status, '')
			xbmc.sleep(10)
		stream.close()
		print "Done pre-compiling"

	def _compile(self):
		print "Waiting to compile segments"
		p=self.segments + 1
		stream = open(self.output_file, 'ab')
		while(p< self.total_segments):
			if p in self.completed:
				infile = '%s_mtstrm.part' % str(p).zfill(3)
				infile = os.path.join(xbmc.translatePath(self.cache_root), infile)
				shutil.copyfileobj(open(infile, 'rb'), stream) 
				print "compiled %s" % p
				os.remove(infile)
				p = p+1
			xbmc.sleep(10)
		print "Done compiling"
	
	def abort(self):
		print "Kill all working threads"
		self.Pool.dismissWorkers(self.threads,do_join=True)
	
	def getCachedStream(self, url):
		cached_stream = self.output_file
		self.pDialog.create('Pre-caching stream')
		self.url = url
		self.getMeta()
		self.Pool = ThreadPool(self.threads, q_size=self.segments)
		self._pre_cache()
		#self.pDialog.create('Pre-compiling stream')
		self.pDialog.close()
		self._pre_compile()
		self.Pool = None
		#xbmc.sleep(500)
		
		#self.compiler = Thread(target=self._compile)
		#self.compiler.start()
		#self.cacher = Thread(target=self._cache)
		#self.cacher.start()
		#self._cache()

		#compiler.join()
		#self._cache()
		#self._compile()

		return True
