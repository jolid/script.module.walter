import os    
from t0mm0.common.addon import Addon
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin


addon = Addon('script.module.walter')
addon_path = addon.get_path()
profile_path = addon.get_profile()
