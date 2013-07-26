import urllib2, re, os, math, sys
import random, time
import htmlcleaner
from threading import Thread
import shutil
import xbmc
import uuid
from threadpool import *

from donnie.settings import Settings
reg = Settings(['plugin.video.theroyalwe', 'script.module.walter'])

class CachingClass:
	def __init__(self, cache_root, DB):
		global reg
		self.DB = DB
		self.cache_root = cache_root
		self.state_file = os.path.join(xbmc.translatePath(self.cache_root), 'state.cache')
		self._cached = 0
		self.total_segments = 0
		self._active_threads = 0
		self.completed = []
		table = [5,8,10,15,20]
		#self.segments = table[int(reg.getSetting('pre-caching-segments'))]
		self.segment_size = 10 * 1000 * 1000		# in Bytes
		self.Done = False
		self.threads = 1 + int(reg.getSetting('max-cache-threads'))
		print "Setting Max Threads: %s" % self.threads
		self.chunk_size = 2 * 1024

	def CreateDirectory(self, dir_path):
		dir_path = dir_path.strip()
		if not os.path.exists(dir_path):
			os.makedirs(dir_path)

	def CleanFileName(self, s, remove_year=True, use_encoding = False, use_blanks = True):
		has_year = re.search('^(.+?)( \(\d{4}\))\.(avi|mkv|flv|mp4)$', s)
		if remove_year and has_year:
			s = "%s.%s" % (has_year.group(1), has_year.group(3))
		s = htmlcleaner.clean(s,strip=True)
		s = s.strip()
		if use_encoding:
			s = s.replace('"', '%22')
			s = s.replace('*', '%2A')
			s = s.replace('/', '%2F')
			s = s.replace(':', ',')
			s = s.replace('<', '%3C')
			s = s.replace('>', '%3E')
			s = s.replace('?', '%3F')
			s = s.replace('\\', '%5C')
			s = s.replace('|', '%7C')
			s = s.replace('&frac12;', '%BD')
			s = s.replace('&#xBD;', '%BD') #half character
			s = s.replace('&#xB3;', '%B3')
			s = s.replace('&#xB0;', '%B0') #degree character		
		if use_blanks:
			s = s.replace('"', ' ')
			s = s.replace('*', ' ')
			s = s.replace('/', ' ')
			s = s.replace(':', ' ')
			s = s.replace('<', ' ')
			s = s.replace('>', ' ')
			s = s.replace('?', ' ')
			s = s.replace('\\', ' ')
			s = s.replace('|', ' ')
			s = s.replace('&frac12;', ' ')
			s = s.replace('&#xBD;', ' ') #half character
			s = s.replace('&#xB3;', ' ')
			s = s.replace('&#xB0;', ' ') #degree character
		return s

	def getMeta(self):
		global reg
		try:
			self.net = urllib2.urlopen(self.url)
			self.headers = self.net.headers.items()
		except urllib2.URLError, e:
			print "*********HTTP Error: %s" % e
			return False
		#print self.headers
		self.total_bytes = int(self.net.headers["Content-Length"])
		#self.segment_size = self.total_bytes / self.threads
		self.total_segments = int(math.ceil(self.total_bytes / self.segment_size))
		try:
			self.filename = str(self.net.headers["Content-Disposition"])
			self.filename = re.search('filename="(.+?)"$', self.filename).group(1)
		except:
			self.filename = self.url.split('/')[-1]
		ext = re.search('(avi|mkv|flv|mp4)$', self.filename, flags=re.IGNORECASE)
		if ext:
			if reg.getBoolSetting('autorename-files'):
				self.filename = "%s.%s" % (self.name, ext.group(1))
		else:
			ext = 'avi'
			self.filename = "%s.%s" % (self.name, ext)
		self.filename = self.CleanFileName(self.filename)
		self.output_file = os.path.join(xbmc.translatePath(self.output_path), self.filename)
		self.update_state(self.qid, 0, self.total_bytes, 0)
		return True

	def update_state(self, qid, bytes, total, threads):
		state = "%s|%s|%s|%s|%s" % (qid, bytes, total, threads, self.uuid)
		fp = open(self.state_file, 'w')
		fp.write(state)
		fp.close()
	
	'''def read_state(self):
		fp = open(self.state_file, 'r')
		state = fp.read()
		fp.close()
		return state'''


	
	def check_state(self):
		#print "Abort?"
		if os.path.exists(self.abort_file):
			#print "Yes"
			self.Health=False
			return False
		#print "No"
		return self.Healthy

	def _monitor(self):
		while not self.Done:
			#print self.check_state()
			if not self.check_state():
				self.AbortAll()
				break
			#print  "Dont abort"
			#print "update state"
			self.update_state(self.qid, self._cached, self.total_bytes, self._active_threads)
			xbmc.sleep(10000)


	def AbortAll(self):
		print "Aborting workers"
		self.Pool.dismissWorkers(self.threads, do_join=False)
		#print "Waiting for workers to abort..."
		self.Done = True
		self.Aborted = True
		self.update_state(-1, 0, 0, 0)
		#shutil.rmtree(self.output_path, True)
		os.remove(self.output_file)

	def _download(self, url, p):
		if not self.check_state():
			return p
		start = p * self.segment_size
		if p == self.total_segments - 1:
			end = self.total_bytes
		else:
			end = (start + self.segment_size) - 1
		r = 'bytes=%s-%s' % (start, end)
		filename = '%s_temp.part' % str(p).zfill(3)
		path = os.path.join(xbmc.translatePath(self.cache_path), filename)

		while True:
			try:
				req = urllib2.Request(url, headers={"Range" : r})
				f = urllib2.urlopen(req)
				break
			except urllib2.URLError, e:
				if not self.check_state():
					return p
				#print "*********HTTP Error: %s" % e
				xbmc.sleep(5000)
				pass
		self._active_threads = self._active_threads + 1
		print "Requesting Segment %s: %s" % (p,r)
		with open(path, 'wb+') as fp:
			while True:
				try:
    					buff = f.read(self.chunk_size)
					if not buff: break
					self._cached = self._cached + len(buff)
					fp.write(buff)
				except:
					print "*********Segment Error: %s" % p
					print "Requeue Segment %s" % p
					p = p * -1
					return p
		return p

		

	def _completed(self, request, result):
		p = result
		if p < 0:
			p = p * -1
			self.Pool.putRequest(WorkRequest(self._download, args=(self.url, p), callback=self._completed))
			self._active_threads = self._active_threads - 1
			return
			
		print "Completed: %s" % p
		self._active_threads = self._active_threads - 1
		self.completed.append(result)
		self.update_state(self.qid, self._cached, self.total_bytes, self._active_threads)

	def _cache(self):
		for p in range(0, self.total_segments):
			self.Pool.putRequest(WorkRequest(self._download, args=(self.url, p), callback=self._completed))
			try:
			    self.Pool.poll()
			except NoResultsPending:
			    pass
		self.Pool.wait()

	def _compile(self):
		print "Waiting to compile segments"
		stream = open(self.output_file, 'wb+')
		p=0
		while(p < self.total_segments):
			if not self.check_state():
				break
			if p in self.completed:
				infile = '%s_temp.part' % str(p).zfill(3)
				infile = os.path.join(xbmc.translatePath(self.cache_path), infile)
				shutil.copyfileobj(open(infile, 'rb'), stream)
				print "Compiled: %s" % p
				os.remove(infile)
				p = p+1
			xbmc.sleep(50)
		stream.close()
		print "Done compiling"


	def Cache(self, qid, name, url, media='', folder=''):
		print "Cache: %s" % url
		if media == 'tvshow':
			if reg.getBoolSetting('cache_tvshow_custom_directory'):
				self.output_path = reg.getSetting('cache_tvshow_directory')
			else:
				self.output_path = os.path.join(xbmc.translatePath(self.cache_root + '/tvshows'), '')
		else:
			if reg.getBoolSetting('cache_movie_custom_directory'):
				self.output_path = reg.getSetting('cache_movie_directory')
			else:
				self.output_path = os.path.join(xbmc.translatePath(self.cache_root + '/movies'), '')
		
		if folder:
			folder = self.CleanFileName(folder)
			self.output_path = os.path.join(xbmc.translatePath(self.output_path + '/' + folder), '')
			self.CreateDirectory(self.output_path)

		self.qid = qid
		self.url = url
		self.name = name
		self.uuid = str(uuid.uuid4())
		self.abort_file = os.path.join(xbmc.translatePath(self.cache_root + '/' + self.uuid), 'abort')
		self.Aborted = False
		self.Healthy = True
		self.cache_path = os.path.join(xbmc.translatePath(self.cache_root  + '/' + self.uuid), '')
		self.CreateDirectory(self.cache_path)

		ok = self.getMeta()
		if not ok:
			self.DB.execute("UPDATE wt_download_queue set status=3 WHERE url=?", [url])
			self.DB.commit()
			return False
		self.Pool = ThreadPool(self.threads)		
		self.DB.execute("UPDATE wt_download_queue set uuid=?, status=1 WHERE url=?", [self.uuid, url])
		self.DB.commit()

		monitor = Thread(target=self._monitor)
		monitor.start()

		compiler = Thread(target=self._compile)
		compiler.start()
		self._cache()
		compiler.join()
		self.Done = True
		monitor.join()
		self.update_state(-1, 0, 0, 0)
		if self.Aborted:
			self.DB.execute("UPDATE wt_download_queue set status=3 WHERE url=?", [url])
		else:
			self.DB.execute("UPDATE wt_download_queue set status=2 WHERE url=?", [url])
		self.DB.commit()
		shutil.rmtree(self.cache_path)
		return self.filename
