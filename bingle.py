#!/usr/bin/env python

import ConfigParser
import re
import json
from optparse import OptionParser

from lib.bingle import Bingle
from lib.mingle import Mingle


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
    product = [config.get('bugzilla', 'product')]
    component = [config.get('bugzilla', 'component')]
    tags = config.get('mingle', 'tags')
    bugzillaProperties = createDictionaryFromPropertiesList(
        config.get('bugzilla', 'properties'))
    mingleProperties = createDictionaryFromPropertiesList(
        config.get('mingle', 'properties'))
    payload = {'method': 'Bug.search', 'params': json.dumps([{
        'product': product,
        'component': component,
        'status': ['UNCONFIRMED', 'NEW'],
        'creation_time': '2012-08-01 00:00 UTC',
    }])}

    bingle = Bingle(payload, debug=debug, picklePath=picklePath, feedUrl=config.get(
        'urls', 'bugzillaFeed'))

    # prepare Mingle instance
    mingle = Mingle(auth, apiBaseUrl)

    for bug in bingle.getBugEntries():
        print bug
        bingle.info("Bug XML: %s" % bug)

        # look for card
        foundBugs = mingle.findCardByName(bugCard, bug.get('summary'))
        bingle.info(mingle.dumpRequest())
        if len(foundBugs) > 0:
            continue

        # retrieve bug comments
        comment_payload = {'method': 'Bug.comments', 'params': json.dumps(
            [{'ids': ['%s' % bug.get('id')]}])}
        comments = bingle.getBugComments(comment_payload, bug.get('id'))
        link = '\n\nFull bug report at https://bugzilla.wikimedia.org/show_bug.cgi?id=%s' % bug.get(
            'id')

        cardParams = {
            'card[name]': '[Bug %s] %s' % (bug.get('id', '---'), bug.get('summary').encode('ascii', 'ignore')),
            'card[card_type_name]': bugCard,
            'card[description]': comments.get('comments')[0].get('text') + link,
            'card[created_by]': auth['username'],
            'card[tags][]': tags  # is not supported by Mingle API currently
        }

        cardLocation = mingle.addCard(cardParams)
        bingle.info(mingle.dumpRequest())

        properties = {}
        for key, value in bugzillaProperties.iteritems():
            properties[value] = bug.get(key, '')

        properties.update(mingleProperties)

        # properties
        for prop, value in properties.iteritems():
            cardParams = {
                'card[properties][][name]': prop,
                'card[properties][][value]': value
            }
            mingle.updateCard(cardLocation, cardParams)

        bingle.info(mingle.dumpRequest())

        # include bug ID if configured as a property
        bugIdFieldName = config.get('mingle', 'bugIdFieldName')
        if len(bugIdFieldName):
            bugId = bug.get('id')
            cardParams = {
                'card[properties][][name]': bugIdFieldName,
                'card[properties][][value]': bugId,
            }
            mingle.updateCard(cardLocation, cardParams)
            bingle.info(mingle.dumpRequest())

    bingle.updatePickleTime()
