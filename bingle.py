#!/usr/bin/env python

import ConfigParser
import re
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
	apiBaseUrl = config.get('urls', 'mingleApiBase')
	bugCard = config.get('mingle', 'bugCard')
	propertiesRaw = config.get('mingle', 'properties')
	properties = dict((key,value) for key,value in (prop.split(',') for prop in propertiesRaw.split(';') if prop.find(',') > -1))	

	bingle = Bingle( debug=debug, picklePath=picklePath, feedUrl=config.get('urls','bugzillaFeed') )

	# prepare Mingle instance
	mingle = Mingle( auth, apiBaseUrl )

	for entry in bingle.getFeedEntries():
		# look for card
		print entry
		foundBugs = mingle.findCardByName( bugCard, entry.title )
		bingle.info( mingle.dumpRequest() ) 
		if len( foundBugs ) > 0:
			continue
		cardParams = {
			'card[name]': entry.title.encode('ascii','ignore'),
			'card[card_type_name]': bugCard,
			'card[description]': entry.id.encode('ascii','ignore'), # URL to bug
			'card[created_by]': auth['username']
		}
		cardLocation = mingle.addCard( cardParams )
		bingle.info( mingle.dumpRequest() ) 

		#properties	
		for prop in properties:
			cardParams = {
				'card[properties][][name]': key,
				'card[properties][][value]': value
			}
			mingle.updateCard( cardLocation, cardParams )
		
		bingle.info( mingle.dumpRequest() )

		# include bug ID if configured as a property
		bugIdFieldName = config.get('mingle','bugIdFieldName')
		if len( bugIdFieldName ):
			bugId = re.search("^\[Bug (\d(.+))\]", title).group(1)
			cardParams = {
				'card[properties][][name]': bugIdFieldName,
				'card[properties][][value]': bugId,
			}
			migle.updateCard( cardLocation, cardParams )
			bingle.info( mingle.dumpRequest() )
	bingle.updatePickleTime()
