#!/usr/bin/env python

import ConfigParser
import re
import json
import requests
import sys
from optparse import OptionParser

from lib.bingle import Bingle
from lib.mingle import Mingle
from bingle import createDictionaryFromPropertiesList

# following 31 lines copied from bingle.py
if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                      help="Path to bingle config file", default="bingle.ini")
    parser.add_option("-p", "--pretend", action="store_true", dest="pretend",
                      default=False, help="Run in 'pretend' mode")
    (options, args) = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(options.config)
    auth = {'username': config.get('auth', 'username'),
            'password': config.get('auth', 'password')}
    debug = config.getboolean('debug', 'debug')
    picklePath = config.get('paths', 'picklePath') + '_resolved'
    apiBaseUrl = config.get('urls', 'mingleApiBase')
    mingleUrlBase = config.get('urls', 'mingleUrlBase')
    bugCard = config.get('mingle', 'bugCard')
    bugIdFieldName = config.get('mingle', 'bugIdFieldName')
    product = config.get('bugzilla', 'product').split(',')
    component = config.get('bugzilla', 'component').split(',')
    bugzillaProperties = createDictionaryFromPropertiesList(
        config.get('bugzilla', 'properties'))
    mingleProperties = createDictionaryFromPropertiesList(
        config.get('mingle', 'properties'))
    mapping = createDictionaryFromPropertiesList(
        config.get('mapping', 'properties'))

    bingle = Bingle(debug=debug, picklePath=picklePath)

    # prepare Mingle instance
    mingle = Mingle(auth, apiBaseUrl)

    fromTime = bingle.getTimeFromPickle()
    bzSearchParams = {
        'product': product,
        'component': component,
        'status': ['RESOLVED'],  # make configurable
    }
    if fromTime:
        bzSearchParams['last_change_time'] = fromTime
        bingle.info(bzSearchParams)
    bugzillaPayload = {
        'method': 'Bug.search',
        'params': json.dumps([bzSearchParams])
    }
    # fetch matching bugs
    bugs = bingle.getBugEntries(bugzillaPayload)
    bingle.info('Number of bugs: %s' % len(bugs))
    counter = 0
    cardsToUpdate = []
    for bug in bugs:
        # see if there's a mingle card matching this bug
        # TODO: refactor this; it's repeated below
        if len(bugIdFieldName) > 0:
            foundBug = mingle.findCardNumByBugId(
                bugCard, bug.get('id'), bugIdFieldName)
        else:
            foundBug = mingle.findCardNumByBugName(
                bugCard, bug.get('id'), bug.get('summary'))
        bingle.info(mingle.dumpRequest())
        if len(foundBug) < 1:
            # eh... we probably want to do something else here
            continue
        cardId = foundBug[0]['Number']
        # figure out the card's status
        # TODO: make 'status' field configurable
        status = mingle.getCardById(cardId).getStatus('Status')
        # TODO: make this list of statuses configurable
        if status not in ['In Development',
                          'Awaiting Final Code Review',
                          'Ready for Signoff',
                          'Accepted']:
            counter += 1
            cardsToUpdate.append(cardId)
            if not pretend:
                # update the card to 'ready for signoff'
                # and make sure it's in this iteration
                cardParams = {
                    'card[properties][][name]': 'Status',
                    'card[properties][][value]': 'Ready for Signoff'
                }
                mingle.updateCard(cardId, cardParams)
                cardParams = {
                    'card[properties][][name]': 'Iteration',
                    'card[properties][][value]': '(Current iteration)'
                }
                mingle.updateCard(cardId, cardParams)
    if not pretend:
        # update pickle
        bingle.updatePickleTime()
        bingle.info('Bug cards updated: %s' % counter)
    else:
        print "Mingle card IDs to update:"
        print cardsToUpdate
