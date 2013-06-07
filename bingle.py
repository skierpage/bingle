#!/usr/bin/env python

import ConfigParser
from optparse import OptionParser
from lib.bingle import Bingle
from lib.mingle import Mingle

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option( "-c", "--config", dest="config",
					help="Path to bingle config file", default="bingle.ini" )
	(options, args) = parser.parse_args()

	config = ConfigParser.ConfigParser()
	config.read( options.config )
	auth = {'username': config.get('auth','username'), 'password': config.get('auth','password')}
	debug = config.getboolean('debug','debug')
	picklePath = config.get('paths', 'picklePath')
	apiBaseUrl = config.get('urls','mingleApiBase')

	bingle = Bingle( debug=debug, picklePath=picklePath, feedUrl=config.get('urls','bugzillaFeed') )

	# prepare Mingle instance
	mingle = Mingle( auth, apiBaseUrl )

	for entry in bingle.getFeedEntries():
		# look for card
		foundBugs = mingle.findCardByName( 'Bug', entry.title )
		bingle.info( mingle.dumpRequest() ) 
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
		bingle.info( mingle.dumpRequest() ) 
		cardParams = {
			'card[properties][][name]': 'status',
			'card[properties][][value]': 'In analysis'
		}
		mingle.updateCard( cardLocation, cardParams )
		bingle.info( mingle.dumpRequest() )
	bingle.updatePickleTime()
