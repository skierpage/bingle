#!/usr/bin/env python

import feedparser, ConfigParser, pickle
from datetime import datetime
from mingle import Mingle
from optparse import OptionParser

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
	parser = OptionParser()
	parser.add_option( "-c", "--config", dest="config",
					help="Path to bingle config file", default="bingle.ini" )
	(options, args) = parser.parse_args()
	config = ConfigParser.ConfigParser()
	# FIXME make this configurable by runtime arg
	config.read( options.config )
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
