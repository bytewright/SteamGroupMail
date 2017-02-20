import configargparse
import logging
import os
import json
import smtplib

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
    parser.add_argument('--debug', help='Debug Mode', action='store_true')
    #parser.set_defaults(DEBUG=True)

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
        items.append(rssitem)
    return items


if __name__ == '__main__':
    args = get_args()
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
    log.info('loading group urls from json...')
    urls_dict = json.load(open(args.urljson, 'r'))

    mail_body = ''
    with open('mail_template.txt', 'r') as f:
        for line in f.readlines():
            mail_body += line

    log.info('loaded mail template:\n'+mail_body)
    for id in urls_dict:
        url = urls_dict[id]['url']
        items = get_rss_tags(url)
        log.info('got {} announcements from rss feed'.format(items.__len__()))
        for key in items[0]:
            mail_body = mail_body.replace('{'+key+'}', items[0][key])

    email_dict = json.load(open(args.emailjson, 'r'))
    recipients = []
    for id in email_dict:
        recipients.append(email_dict[id]['email'])
    log.info('sending mail to {} recipients:\n{}'.format(recipients.__len__(), mail_body))
    send_email(args.smtpusr, args.smtppw, recipients, 'TTSS Mail', mail_body)
