#!/usr/bin/env python

import ConfigParser
import sys
import requests
import re
import json
from optparse import OptionParser
from lib.bingle import Bingle


def getBoardId(baseParams, boardBaseName, debug=False, getLatest=False):
    boardQueryParams = {
        'query': boardBaseName,
        'modelTypes': 'boards',
        'board_fields': 'name'
    }
    payload = dict(baseParams.items() + boardQueryParams.items())
    r = requests.get('https://trello.com/1/search', params=payload)
    # don't try/except because if this fails, we can't go further anyway
    r.raise_for_status()
    boards = r.json()['boards']
    if getLatest:
        return getLatestBoardId(boards, debug)
    else:
        if not len(boards):
            print "No board found by the name %s; exiting." % boardBaseName
            sys.exit(1)
        return boards[0]['id']


def getLatestBoardId(boardsJson, debug=False):
    # sprint names are like 'Mobile App - Sprint 9'; we want to find the latest
    sprintNumRegex = re.compile('sprint (\d+)', re.I)
    boards = []
    for board in boardsJson:
        sprintNum = sprintNumRegex.search(board['name'])
        if sprintNum:
            # do we really need name? may come in handy
            boards.append(
                (int(sprintNum.group(1)),
                    board['id'],
                    board['name'])
            )
    if not len(boards):
        print "There are no valid boards for which to add cards."
        exit(1)
    # pick the biggest sprintNum
    boards.sort()
    boardId = boards[-1][1]
    if debug:
        print "Board name: %s" % boards[-1][2]
    return boardId

if __name__ == "__main__":
    # config stuff
    parser = OptionParser()
    parser.add_option("-c", "--config", dest="config",
                      help="Path to bugello config file", default="bugello.ini")
    (options, args) = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(options.config)
    debug = config.getboolean('debug', 'debug')
    appKey = config.get('trello', 'appKey')
    picklePath = config.get('paths', 'picklePath')
    product = config.get('bugzilla', 'product').split(',')
    component = config.get('bugzilla', 'component').split(',')

    # check for authorization pin - this seems easier than dealing with oAuth
    # note never expiring pin; maybe make this configurable.
    try:
        pin = config.get('trello', 'pin')
    except:
        pin = ''
    if not len(pin):
        pinUrl = "https://trello.com/1/authorize?key=%s&name=%s&expiration=never&response_type=token&scope=read,write" % \
            (appKey, config.get('trello', 'appName'))
        print "You must add a valid Trello user PIN to your config file."
        print "To get a Trello user PIN, visit:"
        print "%s" % pinUrl
        sys.exit(1)

    # params needed by all trello api reqs
    baseParams = {
        'key': appKey,
        'token': pin,
    }

    boardId = getBoardId(baseParams, config.get(
        'trello', 'boardBaseName'), debug, config.getboolean('trello', 'useLatestBoard'))
    # determine current board

    # determine 'Ready for Dev' list
    # @TODO is this *always* the name of the list to use?
    tListUrl = 'https://trello.com/1/boards/%s/lists' % boardId
    r = requests.get(tListUrl, params=baseParams)
    # don't try/except, because we can't do anything without this.
    r.raise_for_status()
    tListId = None
    tListName = config.get('trello', 'targetListName')
    for tList in r.json():
        if tList['name'].lower() == tListName.lower():
            tListId = tList['id']
            if debug:
                print "List id: %s" % tListId
            break
    if not tListId:
        print "Could not find list: %s" % tListName
        sys.exit(1)

    bingle = Bingle(debug=debug, picklePath=picklePath)
    fromTime = bingle.getTimeFromPickle()
    params = {
        'product': product,
        'status': ['UNCONFIRMED', 'NEW']
        'last_change_time': fromTime
    }
    if len(component) > 0:
        params['component'] = component

    bugzillaPayload = {
        'method': 'Bug.search',
        'params': json.dumps([params])
    }

    for entry in bingle.getBugEntries(bugzillaPayload):
        # 1 look for existence of the card
        cardTitle = entry.get('summary').ecode('UTF-8', 'ignore')
        cardQueryParams = {
            'query': cardTitle,
            'card_fields': 'name',
            'modelTypes': 'cards'
        }
        payload = dict(baseParams.items() + cardQueryParams.items())
        try:
            r = requests.get('https://trello.com/1/search', params=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if debug:
                print "Error querying for: %s" % cardTitle
                print "Reason: %s" % e
            continue
        # check if we actually have a match
        # it looks like the API search query might do a fuzzy search, so we want to
        # make sure we only get a full match
        cardExists = False
        for card in r.json()['cards']:
            if card['name'] == cardTitle:
                cardExists = True
        if cardExists:
            if debug:
                print "Card %s already exists." % card['name']
            continue

        bugUrl = 'https://bugzilla.wikimedia.org/%s' % entry.get('id')
        # add card to current board
        newCardParams = {
            'name': cardTitle,
            'desc': bugUrl,
            'idList': tListId,
            'due': None
        }
        payload = dict(baseParams.items() + newCardParams.items())
        try:
            r = requests.post('https://trello.com/1/cards', params=payload)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if debug:
                print "Error adding card: %s" % cardTitle
                print "Reason: %s" % e
            sys.exit(-1)
            continue
    bingle.updatePickleTime()
