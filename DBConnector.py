import logging
from peewee import *

log = logging.getLogger()
db = SqliteDatabase('steamgrpAnnos.db')


class DBConnector:

    def __init__(self, usrname, usrpw, dbhost, dbport):
        self.usrname = usrname
        self.usrpw= usrpw
        self.dbhost = dbhost
        self.dbport = dbport
        self.isConnected = False

    def connect(self):
        log.info('connecting to db')
        db.connect()
        log.info('creating tables in db')
        db.create_table(SendAnnouncement, True)
        self.isConnected = True

    def saveToDb(self, title, guid):
        log.info('querying db')
        entry = SendAnnouncement.create(title=title, guid=guid)
        entry.save()

    def isInDB(self, guid):
        log.info('querying db for guid: '+guid)
        try:
            query = SendAnnouncement.get(SendAnnouncement.guid == guid)
        except:
            return False
        log.info('guid is in db')
        return True


class SendAnnouncement(Model):
    title = CharField()
    guid = CharField()

    class Meta:
        database = db  # This model uses the "people.db" database.
