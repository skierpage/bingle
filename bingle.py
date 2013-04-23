#!/usr/bin/env python

import feedparser, requests, ConfigParser, pickle
from datetime import datetime

class Mingle:
	auth = ()
	apiBaseUrl = ''

	def __init__( self, auth=None, apiBaseUrl=None ):
		if auth is not None:
			self.setAuth( auth )
		if apiBaseUrl is not None:
			self.setApiBaseUrl( apiBaseUrl )

	def setAuth( self, auth ):
		if not isinstance(auth, dict):
			raise TypeError( 'Auth params must be passed as a dictionary.' )
		if not ( auth.has_key('username') or auth.has_key('password')):
			raise NameError( '\'username\' and \'password\' dictionary keys not found.' )
		self.auth = ( auth['username'], auth['password'] )

	def setApiBaseUrl( self, apiBaseUrl ):
		self.apiBaseUrl = apiBaseUrl

	def executeMql( self, mql ):
		payload = { 'mql': mql }
		url = '%s/cards/execute_mql.json' % self.apiBaseUrl
		debug = "URL: %s" % url
		info( debug )
		r = requests.get( url, auth=self.auth, params=payload )
		debug = "Status: %d" % r.status_code
		info( debug )
		r.raise_for_status()
		info( r.json() )
		return r.json()

	def findCardByName( self, cardType, name ):
		mql = 'SELECT number WHERE Type=\'%s\' AND name=\'%s\'' % ( cardType, name.replace("'", "\\'"))
		debug = "MQL: %s" % mql
		info( debug )
		return self.executeMql( mql )

	def addCard( self, cardParams ):
		url = '%s/cards.xml' % self.apiBaseUrl
		debug = "URL: %s" % url
		info( debug )
		r = requests.post( url, auth=self.auth, params=cardParams )
		info( cardParams )
		debug = "Status: %d" % r.status_code
		info( debug )
		r.raise_for_status()
		# should just return card num, not full API URL
		return r.headers['location']

	def updateCard( self, location, cardParams ):
		# should use card num not full API URL
		debug = "URL: %s" % location
		info( debug )
		info (cardParams )
		r = requests.put( location, auth=self.auth, params=cardParams )
		debug = "Status %d" % r.status_code
		info( debug )
		r.raise_for_status()

def info( out ):
	if debug is True:
		print "[INFO] %s" % out

def getBugzillaFeedUrl( feedUrl ):
	now = datetime.now().strftime('%Y-%m-%d %H:%M')
	fromTime = getTimeFromPickle()
	if fromTime is not None:
		feedUrl = feedUrl + '&v1=%s' % fromTime
	pickleTime( now )
	return feedUrl

def getTimeFromPickle():
	try:
		pFile = open( 'bingle.pickle', 'rb' )
		fromTime = pickle.load( pFile )
		pFile.close()
	except:
		fromTime = None
	debug = "From time: %s" % fromTime
	info( debug )
	return fromTime

def pickleTime( timeToPickle ):
	pFile = open( 'bingle.pickle', 'w+b' )
	pickle.dump( timeToPickle, pFile )
	pFile.close()

if __name__ == "__main__":
	config = ConfigParser.ConfigParser()
	# FIXME make this configurable by runtime arg
	config.read( 'bingle.ini' )
	auth = {'username': config.get('auth','username'), 'password': config.get('auth','password')}
	debug = config.getboolean('debug','debug')
	apiBaseUrl = config.get('urls','mingleApiBase')

	# prepare Mingle instance
	mingle = Mingle( auth, apiBaseUrl )

	feedUrl = getBugzillaFeedUrl( config.get('urls','bugzillaFeed') )
	info( feedUrl )
	feed = feedparser.parse( feedUrl )
	info( "Feed length: %d" % len(feed.entries) )

	for entry in feed.entries:
		# look for card
		foundBugs = mingle.findCardByName( 'Bug', entry.title )
		if len( foundBugs ) > 0:
			continue
		cardParams = {
			'card[name]': entry.title.encode('ascii','ignore'),
			'card[card_type_name]':'bug',
			'card[description]': entry.id.encode('ascii','ignore'), # URL to bug
			'card[properties][][name]': 'Iteration',
			'card[properties][][value]': '(Current iteration)',
			'card[created_by]': auth['username']
		}
		cardLocation = mingle.addCard( cardParams )
		cardParams = {
			'card[properties][][name]': 'status',
			'card[properties][][value]': 'In analysis'
		}
		mingle.updateCard( cardLocation, cardParams )
