import sys, os, hashlib
#import urllib2, urllib, sys, os, re, random, copy, shutil
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from t0mm0.common.addon import Addon
from databaseconnector import DatabaseClass
addon = Addon('script.module.walter')
addon_path = addon.get_path()
profile_path = addon.get_profile()
from metahandler import metahandlers
from donnie.settings import Settings
reg = Settings(['script.module.walter'])
cTime=0
tTime=0

class WPlayer (xbmc.Player):
	def __init__ (self,  *args):
		xbmc.Player.__init__(self)
		pass

	def play(self, url, listitem, seekTime=0, strm=False, metadata=None):
		self._seek = seekTime
		self.metadata=metadata
		self._tTime=0
		self._cTime=0
		if strm:
			xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,listitem)
		else:
             		xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, listitem)

	def isplaying(self):
        	xbmc.Player.isPlaying(self)

	def onPlayBackStarted(self):
		print 'Now im playing... '
		xbmc.Player().seekTime(self._seek)

	def onPlayBackEnded(self):
		global profile_path
		print "Now imNow imEnded "
		try:
			self.markWatched(self.metadata['video_type'], self.metadata['title'], self.metadata['imdb_id'], season=self.metadata['season'], episode=self.metadata['episode'])
		except:
			pass
		'''if reg.getBoolSetting('enable-pre-caching'):
			dialog = xbmcgui.Dialog()
			if dialog.yesno("Delete Cache?","Do you want to delete the cache file?"):
				cache_file = os.path.join(xbmc.translatePath(profile_path + '/cache'), 'mtstrm.avi')
				os.remove(cache_file)'''
	def onPlayBackStopped(self):
		global profile_path
		global cTime
		global tTime
		print "Now im Stopped "
		try:
			percent = cTime * 100 / tTime
			if percent > 90:
				self.markWatched(self.metadata['video_type'], self.metadata['title'], self.metadata['imdb_id'], season=self.metadata['season'], episode=self.metadata['episode'])
		except:
			pass

		'''if reg.getBoolSetting('enable-pre-caching'):
			dialog = xbmcgui.Dialog()
			if dialog.yesno("Delete Cache?","Do you want to delete the cache file?"):
				cache_file = os.path.join(xbmc.translatePath(profile_path + '/cache'), 'mtstrm.avi')
				os.remove(cache_file)'''


	def markWatched(self, media_type, title, imdb_id, season='', episode='', year=''):
		try:
			META = metahandlers.MetaData()
			META.change_watched(media_type, title, imdb_id, season=season, episode=episode, year=year, watched=7)	
		except Exception, e:
			print "******* Walter Error: %s" % e
		

class QueueClass:
	def __init__(self):
		global profile_path
		db_file = os.path.join(xbmc.translatePath(profile_path), 'walter.db')
		sql_path = os.path.join(xbmc.translatePath(profile_path + '/resources/database'), '')
		self.DB = DatabaseClass(db_file, sql_path)

	def queue(self, name, url, src, media='', folder=''):
		print "Adding %s: %s to queue" % (media, name)
		try:
			number = self.DB.query("SELECT count(qid) + 1 FROM wt_download_queue WHERE status=0")
			self.DB.execute("INSERT INTO wt_download_queue(type, description, url, src, folder, num) VALUES(?,?,?,?,?,?)", [media, name, url, src, folder, number[0]])
			self.DB.commit()
			return True
		except:
			return False

	def Cancel(self, qid):
		# Implement Stop command here
		self.DB.execute("UPDATE wt_download_queue SET status=-1 WHERE qid=?", [qid])
		#self.DB.commit()

	def clearFailed(self):
		self.DB.execute("DELETE FROM wt_download_queue WHERE status=3 or status=-1")
		self.DB.commit()
		return True

	def clearCompleted(self):
		self.DB.execute("UPDATE wt_download_queue SET status=4 WHERE status=2")
		self.DB.commit()
		return True

	def getQueue(self):
		rows = self.DB.query("SELECT * from wt_download_queue WHERE status > -1 AND status < 4 ORDER BY  status, num ASC", force_double_array=True)
		return rows

	def getStatus(self):
		global profile_path
		status = {}
		number = self.DB.query("SELECT count(qid) FROM wt_download_queue WHERE status=0")
		status['length'] = number[0]
		try:
			state_file = os.path.join(xbmc.translatePath(profile_path + 'cache'), 'state.cache')
			fp = open(state_file, 'r')
			data = fp.read().strip()
			fp.close()
			data = data.split('|')
			name = self.DB.query('SELECT * FROM wt_download_queue WHERE qid=?', [data[0]]) 
			status['name'] = name[2]
			
			status['cached'] = data[1]
			status['total'] = data[2]
			status['threads'] = data[3]
		except:
			pass

		return status
		
	def getQuickStatus(self):
		global profile_path
		status = {}
		state_file = os.path.join(xbmc.translatePath(profile_path + 'cache'), 'state.cache')
		fp = fp = open(state_file, 'r')
		data = fp.read().strip()
		fp.close()
		data = data.split('|')
		status['cached'] = int(data[1])
		status['total'] = int(data[2])
		status['percent'] = 100 * status['cached'] / status['total'] 
		return status
	

class StreamClass:
	def __init__(self, url='', title='', info='', hashid='', hashstring='', metadata=''):
		global profile_path
		self.url = url
		self.title = title
		self.info = info
		self.metadata=metadata
		print "Haststring %s" % hashstring
		if hashstring:
			hashid = self.gethash(hashstring)

		if not hashid:
			self.hashid = self.gethash(url)
		else:
			self.hashid = hashid

		db_file = os.path.join(xbmc.translatePath(profile_path), 'walter.db')
		sql_path = os.path.join(xbmc.translatePath(profile_path + '/resources/database'), '')
		self.DB = DatabaseClass(db_file, sql_path)

	def gethash(self, string):
		print "Expected Haststring %s" % string
    		m = hashlib.md5()
    		m.update(string.encode('utf-8'))
    		return m.hexdigest()


	def play(self, strm=False):
		global cTime
		global tTime
		wp = WPlayer()
		seekTime = 0
		if not reg.getBoolSetting('enable-pre-caching'):
			try:
				test = self.DB.query("SELECT * FROM wt_player_state WHERE hash=?", [self.hashid])
				if test:
					import datetime, math
					cTime = float(test[2])
					resume = str(datetime.timedelta(seconds= math.floor(cTime)))
					dialog = xbmcgui.Dialog()
					if dialog.yesno("Resume playback?","Do you want to resume playback from: %s" % resume):
						seekTime = cTime	
			except:
				pass

		try:
			description = info['description']
		except:
			description = ''

		try:
			thumb = info['thumb']
		except:
			thumb = ''

		try:
			icon = info['icon']
		except:
			icon = ''
		
		listitem = xbmcgui.ListItem(self.title, iconImage=icon, thumbnailImage=thumb, path=str(self.url))

		listitem.setInfo('video', {'Title': self.title, 'plotoutline': description, 'plot': description, 'Genre': description})
		listitem.setThumbnailImage(thumb)
		listitem.setProperty("IsPlayable", "true")

		
		if reg.getBoolSetting('enable-pre-caching'):
			from mtstreaming import MTStreaming
			MTS = MTStreaming()
			cached_stream = MTS.getCachedStream(self.url)
			self.url = cached_stream
			strm=False	


		wp.play(self.url, listitem, seekTime, strm=strm, metadata=self.metadata)
		currentTime = 0
 		try:
        		tTime = wp.getTotalTime()
    		except Exception:
        		xbmc.sleep(5000)
        	try:
            		tTime = wp.getTotalTime()
        	except Exception, e:
            		print 'Error grabbing video time: %s' % e
            		return False

    		while(wp.isplaying()):
        		try:
				tTime = wp.getTotalTime()
            			cTime = wp.getTime()
        		except Exception:
           			break
        		xbmc.sleep(1000)
		try:
    			percent = int(cTime * 100 / tTime )
		except:
			percent = 0
		if percent >= 97:
			self.DB.execute("DELETE FROM wt_player_state WHERE hash=?", [self.hashid])
		else:
			self.DB.execute("REPLACE INTO wt_player_state(hash, current, total, percent) VALUES(?,?,?,?)", [self.hashid, cTime, tTime, percent]) 
		self.DB.commit()

