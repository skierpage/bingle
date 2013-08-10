#!/usr/bin/env python

import ConfigParser
import re
import json
from optparse import OptionParser

from lib.bingle import Bingle
from lib.mingle import Mingle
from htmlparser import BugzillaSummaryTableParser


def createDictionaryFromPropertiesList(properties):
	return dict((key, value) for key, value in (prop.split(',')
							   for prop in properties.split(';') if prop.find(',') > -1))

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--config", dest="config",
					  help="Path to bingle config file", default="bingle.ini")
	(options, args) = parser.parse_args()

	config = ConfigParser.ConfigParser()
	config.read(options.config)
	auth = {'username': config.get('auth', 'username'), 
	'password': config.get('auth', 'password')}
	debug = config.getboolean('debug', 'debug')
	picklePath = config.get('paths', 'picklePath')
	apiBaseUrl = config.get('urls', 'mingleApiBase')
	bugCard = config.get('mingle', 'bugCard')
	tags = config.get('mingle', 'tags')
	bugzillaProperties = createDictionaryFromPropertiesList(config.get('bugzilla', 'properties'))
	mingleProperties =createDictionaryFromPropertiesList(config.get('mingle', 'properties'))
	payload = {'method':'Bug.search','params':json.dumps([{
		'product':['Mediawiki extensions'],
		'component':['MobileFrontend'],
		'status':['UNCONFIRMED','NEW'],
		'creation_time':'2012-08-01 00:00 UTC',
		'include_fields':bugzillaProperties.keys()}])}
	
	bingle = Bingle(payload, debug=debug, picklePath=picklePath, feedUrl=config.get(
		'urls', 'bugzillaFeed'))
	
	# prepare Mingle instance
	mingle = Mingle(auth, apiBaseUrl)

	for bug in bingle.getFeedEntries():
		# look for card
		bingle.info("Bug XML: %s" % bug)

		# bugzilla.clean_data()
		# if len(bugzillaProperties) > 0:
		#     bugzilla.feed(entry.summary)
		#     bugProperties = bugzilla.data
		# else:
		#     bugProperties = []
		# bugProperties.extend(properties)
		print bug
		foundBugs = mingle.findCardByName(bugCard, bug.get('summary'))
		bingle.info(mingle.dumpRequest())
		if len(foundBugs) > 0:
			continue
		cardParams = {
			'card[name]': bug.get('summary').encode('ascii', 'ignore'),
			'card[card_type_name]': bugCard,
			'card[description]': bug.get('id'), #.encode('ascii', 'ignore'),  # URL to bug
			'card[created_by]': auth['username'],
			'card[tags][]': tags # is not supported by Mingle API currently
		}
		cardLocation = mingle.addCard(cardParams)
		bingle.info(mingle.dumpRequest())

		properties = dict(bugzillaProperties.items() + mingleProperties.items())

		# properties
		for prop, value in properties.iteritems():
			print prop,value
			cardParams = {
				'card[properties][][name]': prop,
				'card[properties][][value]': value
			}
			mingle.updateCard(cardLocation, cardParams)

		bingle.info(mingle.dumpRequest())

		# include bug ID if configured as a property
		bugIdFieldName = config.get('mingle', 'bugIdFieldName')
		if len(bugIdFieldName):
			bugId = re.search("^\[Bug (\d(.+))\]", entry.title).group(1)
			cardParams = {
				'card[properties][][name]': bugIdFieldName,
				'card[properties][][value]': bugId,
			}
			mingle.updateCard(cardLocation, cardParams)
			bingle.info(mingle.dumpRequest())
	bingle.updatePickleTime()
