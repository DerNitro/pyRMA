"""
Модуль отправки почтовыйх сообщений.
"""
from acs import schema, log
import sqlalchemy.orm
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


class Mail:
    mail_from = None
    mail_to = None
    mail_cc = None

    def __init__(self, engine):
        with schema.db_select(engine) as db:
            try:
                self.host = db.query(schema.Parameter.value).filter(schema.Parameter.name == 'EMAIL_HOST').one()[0]
            except sqlalchemy.orm.exc.NoResultFound:
                self.host = '127.0.0.1'
            try:
                self.port = int(db.query(schema.Parameter.value).filter(schema.Parameter.name == 'EMAIL_PORT').one()[0])
            except sqlalchemy.orm.exc.NoResultFound:
                self.port = 25
            try:
                self.type = db.query(schema.Parameter.value).filter(schema.Parameter.name == 'EMAIL_TYPE').one()[0]
            except sqlalchemy.orm.exc.NoResultFound:
                self.type = 'SMTP'
            try:
                self.mail_from = db.query(schema.Parameter.value).filter(schema.Parameter.name == 'EMAIL_FROM').one()[0]
            except sqlalchemy.orm.exc.NoResultFound:
                self.mail_from = 'acs@localhost'

    def send(self, template, **data):
        if self.host:
            pass
        print(template.format(**data))

    def __repr__(self):
        return "{0}".format(self.__dict__)


def send_mail(engine, template, data):
    mail = Mail(engine)
    user_id = data['user']
    with schema.db_select(engine) as db:
        mail.mail_to = db.query(schema.User.email).filter(schema.User.login == user_id).one()[0]
    mail.send(template, **data)
