import pickle
import requests
import feedparser
from datetime import datetime


class Bingle:

    def __init__(self, payload, picklePath='bingle.pickle', debug=False, feedUrl=None):
        self.payload = payload
        self.setDebug(debug)
        self.setPicklePath(picklePath)
        if feedUrl is not None:
            self.setFeedUrl(feedUrl)

    def setPicklePath(self, picklePath):
        self.picklePath = picklePath
        debug = "Pickle path: %s" % picklePath
        self.info(debug)

    def setDebug(self, debug):
        if not isinstance(debug, bool):
            raise TypeError('Debug param must be a boolean')
        self.debug = debug

    def info(self, out):
        if self.debug is True:
            print "[INFO] %s" % out

    def getBugzillaFeedUrl(self, feedUrl):
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        fromTime = self.getTimeFromPickle()
        if fromTime is not None:
            feedUrl = feedUrl + '&v1=%s' % fromTime
        self.newPickleTime = now
        return feedUrl

    def getTimeFromPickle(self):
        try:
            pFile = open(self.picklePath, 'rb')
            fromTime = pickle.load(pFile)
            pFile.close()
        except:
            self.info("Pickle file could not be opened")
            fromTime = None
        debug = "From time: %s" % fromTime
        self.info(debug)
        return fromTime

    def updatePickleTime(self, time=None):
        if not time:
            time = self.newPickleTime
        debug = "Pickling time: %s" % time
        self.info(debug)
        self.pickleTime(time)

    def pickleTime(self, timeToPickle):
        pFile = open(self.picklePath, 'w+b')
        pickle.dump(timeToPickle, pFile)
        pFile.close()

    def getFeedEntries(self):
        feed = feedparser.parse(self.feedUrl)
        self.info("Number of bugs found: %d" % len(feed.entries))
        return feed

    def getBugEntries(self)
        response = requests.get('https://bugzilla.wikimedia.org/jsonrpc.cgi', params=self.payload) 
        # print response.json()
        self.info("Number of bugs found: %d" % len(response.json().get('result',{}).get('bugs')))
        return response.json().get('result',{}).get('bugs', {})

    def setFeedUrl(self, feedUrl):
        self.feedUrl = self.getBugzillaFeedUrl(feedUrl)
        self.info(self.feedUrl)
