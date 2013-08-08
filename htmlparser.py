from HTMLParser import HTMLParser


class BugzillaSummaryTableParser(HTMLParser):

    def __init__(self, properties):
        HTMLParser.__init__(self)
        self.properties = dict((key, value) for key, value in (prop.split(',')
                               for prop in properties.split(';') if prop.find(',') > -1))
        self.data = []
        self.in_td = 0
        self.tr_name = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.tr_name = attrs[0][1] if len(attrs) > 0 else None
        elif tag == 'td':
            self.in_td += 1

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.in_td = 0
            self.tr_name = None

    def handle_data(self, data):
        if self.in_td == 2 and self.tr_name != None and self.tr_name in self.properties:
            data = data.strip('\n')
            if data != '':
                self.data.append((self.properties.get(self.tr_name), data))

    def clean_data(self):
        self.data = []
        self.in_td = 0
        self.tr_name = None
