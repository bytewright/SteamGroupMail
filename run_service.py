import configargparse
import logging
import os
import json
import smtplib
import time

from django import db

from DBConnector import DBConnector
from urllib.request import urlopen
from lxml import etree

logFormatter = logging.Formatter("%(asctime)s [%(module)14s] [%(levelname)5s] %(message)s")
log = logging.getLogger()
log.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


def get_args():
    configpath = os.path.join(os.path.dirname(__file__), 'config.ini')
    parser = configargparse.ArgParser(default_config_files=[configpath])
    parser.add_argument('--urljson', type=str,
                        help='json file, containing rss-feeds')
    parser.add_argument('--emailjson', type=str,
                        help='json file, containing recipients')
    parser.add_argument('--smtpaddr', type=str,
                        help='address of mail server')
    parser.add_argument('--smtpport', type=int,
                        help='port of mail server')
    parser.add_argument('--smtpusr', type=str,
                        help='user login for mail server')
    parser.add_argument('--smtppw', type=str,
                        help='password for mail server')
    parser.add_argument('--dbaddr', type=str,
                        help='address of db')
    parser.add_argument('--dbusr', type=str,
                        help='user login for db')
    parser.add_argument('--dbpw', type=str,
                        help='password for db')
    parser.add_argument('--loopTime', type=int,
                        help='time between loop runs in seconds')
    parser.add_argument('--debug', help='Debug Mode', action='store_true')

    return parser.parse_args()


def send_email(gmail_user, gmail_pwd, recipient, subject, body):
    FROM = gmail_user
    TO = recipient if type(recipient) is list else [recipient]
    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), subject, body)
    try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo()
        server_ssl.login(gmail_user, gmail_pwd)
        server_ssl.sendmail(FROM, TO, message)
        server_ssl.close()
        log.info('successfully sent the mail')
    except:
        log.error("failed to send mail")


def get_rss_tags(url):
    items = []
    steam_rss = urlopen(url).read()
    group_announcements = etree.fromstring(steam_rss)
    for item in group_announcements.xpath('/rss/channel/item'):
        rssitem = {}
        rssitem['title'] = item.xpath("./title/text()")[0]
        rssitem['description'] = item.xpath("./description/text()")[0]
        rssitem['link'] = item.xpath("./link/text()")[0]
        rssitem['pubDate'] = item.xpath("./pubDate/text()")[0]
        rssitem['guid'] = item.xpath("./guid/text()")[0]
        items.append(rssitem)
    return items


if __name__ == '__main__':
    args = get_args()
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    fileHandler = logging.FileHandler('steamGrpService.log')
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)

    # loading data
    dbcon = DBConnector(args.dbusr, args.dbpw, args.dbaddr, 1000)
    dbcon.connect()

    log.info('loading group urls from json...')
    urls_dict = json.load(open(args.urljson, 'r'))

    log.info('loading mail template')
    mail_body = ''
    with open('mail_template.txt', 'r') as f:
        for line in f.readlines():
            mail_body += line

    log.info('loading email recipients')
    email_dict = json.load(open(args.emailjson, 'r'))
    recipients = []
    for id in email_dict:
        recipients.append(email_dict[id]['email'])
    log.debug(recipients)

    log.info('starting main loop')
    while True:
        items = []
        for id in urls_dict:
            url = urls_dict[id]['url']
            items = items + get_rss_tags(url)

        log.info('got {} announcements from rss feed'.format(items.__len__()))
        for item in items:
            if not dbcon.isInDB(item['guid']):
                new_mail = mail_body
                for key in item:
                    new_mail = new_mail.replace('{' + key + '}', item[key])
                log.info('sending mail to {} recipients:\n{}'.format(recipients.__len__(), mail_body))
                send_email(args.smtpusr, args.smtppw, recipients, 'TTSS Mail', new_mail)
                log.info('adding send announcement to db:\n{}'.format(item['guid']))
                dbcon.saveToDb(item['title'], item['guid'])
        time.sleep(args.loopTime)
