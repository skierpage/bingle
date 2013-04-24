import requests

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

