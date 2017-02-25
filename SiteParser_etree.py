import logging
from urllib.request import urlopen
from xml.etree import ElementTree as ET

log = logging.getLogger()


class SiteParser:
    def __init__(self):
        self.name = 'rss_parser'
        self.canParse = ['rss', 'file_xml']
        self.tags = ['uniqueId', 'title', 'description', 'link', 'pubDate']

    def get_item_list(self, url, url_type):
        if url_type not in self.canParse:
            log.error('no method can handle url of type {}:\n{}'.format(url_type, url))
            return []
        log.debug('start parsing of item with type: {}'.format(url_type))
        item_list = []
        if url_type == 'rss':
            item_list = self.get_rss_tags(self.get_rss_content(url))
        if url_type == 'file_xml':
            item_list = self.get_rss_tags(self.get_file_content(url))
        if url_type == 'forum':
            item_list = self.get_forum_tags(url)
        return item_list

    def get_rss_tags(self, steam_rss):
        items = []
        xml_root = ET.fromstring(steam_rss)
        for item in xml_root.iter('item'):
            rssitem = {}
            for child in item:
                if child.tag == 'guid':
                    rssitem['uniqueId'] = '{}'.format(child.text).split('/')[-1]
                if child.tag in self.tags:
                    rssitem[child.tag] = child.text
            items.append(rssitem)
        return items

    def get_rss_content(self, url):
        log.debug('parsing url:\n{}'.format(url))
        urlcontent = urlopen(url).read()
        log.debug('{}'.format(urlcontent))
        return urlcontent

    def get_file_content(self, filepath):
        content = ''
        with open(filepath, 'r') as f:
            for line in f.readlines():
                content += line
        return content

    def get_forum_tags(self, url):
        return {}
