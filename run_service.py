import configargparse
import logging
import os
import json
import smtplib
import time

from DBConnector import DBConnector
from SiteParser import SiteParser

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
    parser.add_argument('--loopTime', type=int,
                        help='time between loop runs in seconds')
    parser.add_argument('--debug', help='Debug Mode', action='store_true')

    return parser.parse_args()


def send_email(gmail_user, gmail_pwd, recipient, subject, body):
    recipients = recipient if type(recipient) is list else [recipient]
    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (gmail_user, ", ".join(recipients), subject, body)
    log.info('sending mail to {} recipients:\n{}'.format(recipients.__len__(), message))
    try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo()
        server_ssl.login(gmail_user, gmail_pwd)
        server_ssl.sendmail(gmail_user, recipients, message)
        server_ssl.close()
        log.info('successfully sent the mail')
    except:
        log.error("failed to send mail")


def send_mail_for_each_item(new_items):
    log.info('loading email recipients')
    recipients = []
    with open(args.emailjson, 'r') as f:
        email_dict = json.load(f)
        for entry_id in email_dict:
            recipients.append(email_dict[entry_id]['email'])
    log.debug(recipients)

    log.info('loading mail template')
    new_mail = ''
    with open('mail_template.txt', 'r') as f:
        for line in f.readlines():
            new_mail += line
    log.debug(new_mail)

    for item in new_items:
        if dbconnection.isInDB(item['uniqueId']):
            continue
        for key in item:
            text_replacement = '{' + key + '}'
            if new_mail.__contains__(text_replacement):
                new_mail = new_mail.replace('{' + key + '}', item[key])
            else:
                log.error('mail template has no placeholder: '+text_replacement)
                new_mail += '{}: {}'.format(key, item[key])

        send_email(args.smtpusr, args.smtppw, recipients, 'TTSS Mail', new_mail)

        log.info('adding send announcement to db:\n{}'.format(item['uniqueId']))
        dbconnection.saveToDb(item['title'], item['uniqueId'])


if __name__ == '__main__':
    args = get_args()
    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    fileHandler = logging.FileHandler('steamGrpService.log')
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)

    # preparing objects
    dbconnection = DBConnector()
    dbconnection.connect()
    parser = SiteParser()

    log.info('starting main loop')
    while True:
        items = []
        with open(args.urljson, 'r') as f:
            log.debug('loading group urls from json...')
            urls_dict = json.load(f)
            for id in urls_dict:
                if urls_dict[id]['type'] in parser.canParse:
                    items = items + parser.get_tags_dict(urls_dict[id]['url'])

        log.info('got {} announcements from rss feed'.format(items.__len__()))
        send_mail_for_each_item(items)
        log.info('sleeping for {} seconds...'.format(args.loopTime))
        time.sleep(args.loopTime)
