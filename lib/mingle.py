import requests
from urlparse import urljoin

class Mingle:
	auth = ()
	apiBase = '' # http://mingle.corp.wikimedia.org/api/v2/projects/mobile
	mrequest = None # active MingleRequest object

	def __init__( self, auth=None, apiBase=None ):
		if auth is not None:
			self.setAuth( auth )
		if apiBase is not None:
			self.setApiBase( apiBase )

	def setAuth( self, auth ):
		if not isinstance(auth, dict):
			raise TypeError( 'Auth params must be passed as a dictionary.' )
		if not ( auth.has_key('username') or auth.has_key('password')):
			raise NameError( '\'username\' and \'password\' dictionary keys not found.' )
		self.auth = ( auth['username'], auth['password'] )

	def setApiBase( self, apiBase ):
		self.apiBase = apiBase

	def executeMql( self, mql ):
		reqUrl = self.getFullApiReqUrl( 'cards/execute_mql.json' )
		payload = {'mql':mql.encode('ascii','ignore')}
		self.mrequest = MingleRequest( reqUrl, payload=payload, auth=self.auth )
		r = self.mrequest.makeRequest()
		r.raise_for_status()
		return r.json()

	def findCardByName( self, cardType, name ):
		# Mingle removes extraneous spaces mid-string; do the same here
		name = ' '.join(name.split())
		mql = 'SELECT number WHERE Type=\'%s\' AND name=\'%s\'' % ( cardType, name.replace("'", "\\'"))
		return self.executeMql( mql )

	def addCard( self, cardParams ):
		reqUrl = self.getFullApiReqUrl( 'cards.xml' )
		self.mrequest = MingleRequest( reqUrl=reqUrl, payload=cardParams, auth=self.auth )
		r = self.mrequest.makeRequest( 'post' )
		r.raise_for_status()
		return r.headers['location']

	def updateCard( self, location, cardParams ):
		# should use card num not full API URL
		self.mrequest = MingleRequest( reqUrl=location, payload=cardParams, auth=self.auth )
		r = self.mrequest.makeRequest( 'put' )
		r.raise_for_status()

	def getFullApiReqUrl( self, apiResourceUrl ):
		return urljoin( self.apiBase, apiResourceUrl ) 

	def getMingleRequestObject( self ):
		return self.mrequest

	def dumpRequest( self ):
		return str( self.getMingleRequestObject() ) 

class MingleRequest:
	payload = {}
	auth = ()
	reqUrl = ''

	def __init__( self, reqUrl=None, payload=None, auth=None ):
		if reqUrl is not None:
			self.reqUrl = reqUrl
		if payload is not None:
			self.payload = payload
		if auth is not None:
			self.auth = auth

	def makeRequest( self, proto='get', reqUrl=None ):
		if reqUrl is None:
			reqUrl = self.reqUrl

		if proto == 'get':
			return self.__makeGetRequest( reqUrl )
		elif proto == 'put':
			return self.__makePutRequest( reqUrl )
		elif proto == 'post':
			return self.__makePostRequest( reqUrl )
		else:
			return None

	def __makeGetRequest( self, reqUrl ):
		r = requests.get( reqUrl, auth=self.auth, params=self.payload )
		return r

	def __makePutRequest( self, reqUrl ):
		r = requests.put( reqUrl, auth=self.auth, params=self.payload )
		return r

	def __makePostRequest( self, reqUrl ):
		r = requests.post( reqUrl, auth=self.auth, params=self.payload )
		return r

	def __str__( self ):
		return "MingleRequest obj:\n%s: %s\n%s: %s" % ('reqUrl', self.reqUrl, 'payload', str( self.payload ))
