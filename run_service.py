# -*- coding: utf-8 -*-

import configargparse
import logging
import os
import json
import smtplib
import time
import re
import string

from DBConnector import DBConnector
from SiteParser_etree import SiteParser


logFormatter = logging.Formatter("%(asctime)s [%(module)14s] [%(levelname)5s] %(message)s")
log = logging.getLogger()
log.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
log.addHandler(consoleHandler)


def get_args():
    configpath = os.path.join(os.path.dirname(__file__), 'data/config.ini')
    configparser = configargparse.ArgParser(default_config_files=[configpath])
    configparser.add_argument('--urljson', type=str,
                        help='json file, containing rss-feeds')
    configparser.add_argument('--emailjson', type=str,
                        help='json file, containing recipients')
    configparser.add_argument('--mailtemplate', type=str,
                        help='text file, containing a template for each mail')
    configparser.add_argument('--smtpaddr', type=str,
                        help='address of mail server')
    configparser.add_argument('--smtpport', type=int,
                        help='port of mail server')
    configparser.add_argument('--smtpusr', type=str,
                        help='user login for mail server')
    configparser.add_argument('--smtppw', type=str,
                        help='password for mail server')
    configparser.add_argument('--loopTime', type=int,
                        help='time between loop runs in seconds')
    configparser.add_argument('--debug', help='Debug Mode', action='store_true')

    return configparser.parse_args()


def clean_text(urlcontent):
    tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')
    urlcontent = urlcontent.replace('<br>', '\n')
    content = tag_re.sub('', urlcontent)
    #remove umlaute
    table = {
        ord('ä'): 'ae',
        ord('ö'): 'oe',
        ord('ü'): 'ue',
        ord('ß'): 'ss',
        ord('Ä'): 'Ae',
        ord('Ö'): 'Oe',
        ord('Ü'): 'Ue',
    }
    content = content.translate(table)
    #remove everything not ascii
    return ''.join(filter(lambda x: x in set(string.printable), content))


def send_email(gmail_user, gmail_pwd, recipient, subject, body):
    recipients = recipient if type(recipient) is list else [recipient]

    message = 'From: {}\nSubject: {}\n\n{}'.format(gmail_user,
                                                   subject,
                                                   body)

    log.info('sending mail to {} recipients:\n{}'.format(recipients.__len__(), message))
    try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo()
        server_ssl.login(gmail_user, gmail_pwd)
        server_ssl.sendmail(gmail_user, recipients, message)
        server_ssl.close()
        log.info('successfully sent the mail')
        return True
    except:
        log.error("failed to send mail")
        return False


def send_mail_for_each_item(new_items):
    log.info('loading email recipients')
    recipients = []
    with open(args.emailjson, 'r') as f:
        email_dict = json.load(f)
        for entry_id in email_dict:
            recipients.append(email_dict[entry_id]['email'])
    log.debug(recipients)

    log.info('loading mail template')
    mail_template = ''
    with open(args.mailtemplate, 'r') as f:
        for line in f.readlines():
            mail_template += line
    log.debug(mail_template)

    for item in new_items:
        new_mail = mail_template
        if dbconnection.isInDB(item['uniqueId']):
            continue
        for key in item:
            text_replacement = '{' + key + '}'
            if new_mail.__contains__(text_replacement):
                new_mail = new_mail.replace('{' + key + '}', clean_text(item[key]))
            else:
                log.error('mail template has no placeholder: '+text_replacement)
                new_mail += '{}: {}'.format(key, clean_text(item[key]))

        if send_email(args.smtpusr, args.smtppw, recipients, 'TTSS Mail', new_mail):
            log.info('adding send announcement to db:\n{}'.format(item['uniqueId']))
            dbconnection.saveToDb(item['title'], item['uniqueId'])
        else:
            log.error('send_mail failed')


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
            for url_id in urls_dict:
                if urls_dict[url_id]['type'] in parser.canParse:
                    items = items + parser.get_item_list(urls_dict[url_id]['url'], urls_dict[url_id]['type'])

        log.info('got {} announcements from rss feed'.format(items.__len__()))
        if items.__len__() > 0:
            send_mail_for_each_item(items)
        log.info('sleeping for {} seconds...'.format(args.loopTime))
        time.sleep(args.loopTime)
