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

from pyrmalib import applib, schema, parameters, access
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mail:
    mail_from = None    # type: str
    mail_to = []
    mail_cc = []
    subject = '[pyRMA]: '

    def __init__(self, param: parameters.Parameters):
        self.host = param.email['host']
        self.port = param.email['port']
        self.type = param.email['type']
        self.mail_from = param.email['from']
        self.log = param.log


    def send(self, template, data):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.subject
        msg['From'] = self.mail_from
        msg['To'] = ",".join(self.mail_to)
        msg['Cc'] = ",".join(self.mail_cc)
        part = MIMEText(template.format(**data))
        msg.attach(part)
        try:
            s = smtplib.SMTP(host=self.host, port=self.port)
            s.sendmail(self.mail_from, self.mail_to, msg.as_string())
            s.quit()
        except smtplib.SMTPServerDisconnected as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPSenderRefused as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPDataError as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPConnectError as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPAuthenticationError as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPHeloError as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPResponseException as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPRecipientsRefused as e:
            self.log.warning(e)
            return False
        except smtplib.SMTPNotSupportedError as e:
            self.log.warning(e)
            return False
        except OSError as e:
            self.log.warning(e)
            return False
        return True

    def __repr__(self):
        return "{0}".format(self.__dict__)


def send_mail(param: parameters.Parameters, subject, template, user: schema.User or list, data, admin_cc=False):
    mail = Mail(param)
    mail.subject += subject
    if admin_cc:
        admins = applib.get_admin_users(param)
        for a in admins:
            mail.mail_cc.append(a.email)
    
    if isinstance(user, list):
        for i in user:
            mail.mail_to.append(i.email)
    elif isinstance(user, schema.User):
        mail.mail_to.append(user.email)
        if isinstance(param.user_info, schema.User) and param.user_info != user:
            mail.mail_cc.append(param.user_info.email)

    if not mail.send(template, data):
        del mail
        return False
    del mail
    return True
