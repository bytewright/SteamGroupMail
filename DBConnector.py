import logging
from peewee import *

log = logging.getLogger()
db = SqliteDatabase('steamgrpAnnos.db')


class DBConnector:

    def __init__(self):
        self.isConnected = False

    def connect(self):
        log.info('connecting to db')
        db.connect()
        log.info('creating tables in db')
        db.create_table(SendAnnouncement, True)
        self.isConnected = True

    def saveToDb(self, title, unique_id):
        log.info('querying db')
        entry = SendAnnouncement.create(title=title, uniqueId=unique_id)
        entry.save()

    def isInDB(self, unique_id):
        log.info('querying db for uniqueId: ' + unique_id)
        try:
            result = SendAnnouncement.get(SendAnnouncement.uniqueId == unique_id)
        except:
            return False
        log.info('uniqueId is in db with title: ' + result.title)
        return True


class SendAnnouncement(Model):
    title = CharField()
    uniqueId = CharField()

    class Meta:
        database = db
