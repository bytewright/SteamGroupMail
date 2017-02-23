import logging
from urllib.request import urlopen
from lxml import etree
from peewee import *

log = logging.getLogger()
db = SqliteDatabase('steamgrpAnnos.db')


class SiteParser:
    def __init__(self):
        self.name = 'rss_parser'
        self.canParse = ['rss']

    def get_tags_dict(self, url):
        items = []
        steam_rss = urlopen(url).read()
        group_announcements = etree.fromstring(steam_rss)
        for item in group_announcements.xpath('/rss/channel/item'):
            rssitem = {'title': item.xpath("./title/text()")[0],
                       'description': item.xpath("./description/text()")[0],
                       'link': item.xpath("./link/text()")[0],
                       'pubDate': item.xpath("./pubDate/text()")[0],
                       'uniqueId': '{}'.format(item.xpath("./guid/text()")[0]).split('/')[-1]}
            items.append(rssitem)
        log.info('{}: found {} items in rss feed'.format(self.name, items.__len__()))
        log.debug(steam_rss)
        log.debug(rssitem)
        return items

