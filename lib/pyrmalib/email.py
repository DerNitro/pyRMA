"""
       Copyright 2016 Sergey Utkin utkins01@gmail.com

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

"""
Модуль отправки почтовыйх сообщений.
"""
from pyrmalib import schema, log
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
                self.mail_from = 'pyrmalib@localhost'

    def send(self, template, **data):
        if self.host:
            pass
        print(template.format(**data))

    def __repr__(self):
        return "{0}".format(self.__dict__)


def send_mail(engine, template, user_id, data):
    mail = Mail(engine)
    user_id = user_id
    with schema.db_select(engine) as db:
        mail.mail_to = db.query(schema.User.email).filter(schema.User.login == user_id).one()[0]
    mail.send(template, **data)