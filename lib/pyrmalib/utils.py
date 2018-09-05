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

import os
import ipaddress


def get_app_parameters(table_parameter, param):
    """
    Возвращает параметры из таблицы.
    :param table_parameter: Таблица schema.Parameter
    :param param: Параметр
    :return: Значение
    """
    return list(filter(lambda x: x.name == param, table_parameter))[0].value


def check_license(lic):
    """
    Проверка валидности файла лицензии

    :param lic: путь к файлу лицензии string
    :type lic:  str
    :return: Возвращает Истина если файл валидный.
    """
    from platform import system
    from socket import gethostname
    import hashlib
    import datetime

    f = open(lic, 'r', encoding='utf-8')
    allhash, idhost, hostname, platform, days = str(f.readline()).split()
    f.close()

    if not system() == platform:
        return False
    if not hashlib.md5(os.popen('hostid').read().strip().encode()).hexdigest() == idhost:
        return False
    if not gethostname() == hostname:
        return False
    if not datetime.datetime.now() < datetime.datetime.strptime(days, '%d/%m/%Y'):
        return False
    if not allhash == hashlib.md5(str(hashlib.md5(os.popen('hostid').read().strip().encode()).hexdigest()).encode() \
                                          + str(gethostname()).encode() \
                                          + str(system()).encode() \
                                          + str(days).encode()).hexdigest():
        return False
    return True


def check_ip(user_ip, ip_address):
    """
    Проверка вхождения IP адреса в разрешенную сеть.

    :param user_ip: IP адрес клиента
    :type user_ip: str
    :param ip_address:  Строка со списком адресов, разделитель ';'
    :type ip_address: str
    :return: Возвращает истину/ложь вхождения IP клиента в список разрешенных адресов
    """
    ips = ip_address.split(';')
    user_ip = ipaddress.ip_address(user_ip)
    for ip in ips:
        try:
            if user_ip in ipaddress.ip_network(ip):
                return True
            else:
                pass
        except ipaddress.NetmaskValueError:
            try:
                if user_ip == ipaddress.ip_address(ip):
                    return True
            except ipaddress.AddressValueError():
                return False
        except ValueError:
            return False

    return False


def valid_ip(ip_addr):
    """
    Проверка корректности IP адреса
    :param ip: str
    :return: true|false
    """
    try:
        ip, port = str(ip_addr).split(':')
    except ValueError:
        ip = ip_addr
        port = 0

    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False

    try:
        int(port)
    except ValueError:
        return False

    return True


def password(passwd, magic, action):
    """
    Функция маскировки/демаскировки пароля

    :param passwd: Исходный пароль
    :type passwd: str
    :param magic: Магическое число
    :type magic: int
    :param action: кодирование/декодирование
    :type action: bool
    :return: Возвращает преобразованый пароль
    """
    c_h = 'PQRabc=>?@[\]defghijkopqJKLrstuv&\'wxy234789!"#$%()*+z01,-./:;<}~ABCDlmnEFGHI56MNOST^_`{|UVWXYZ'
    result = ''
    magic = list(str(magic))
    if set(passwd).issubset(set(c_h)):
        if action:
            passwd = list(passwd)
            magic.reverse()
            for i in magic:
                try:
                    assert passwd[int(i)]
                    a = passwd.pop()
                    passwd.insert(int(i), a)
                except IndexError:
                    pass
        else:
            passwd = list(passwd)
            for i in magic:
                try:
                    a = passwd[int(i)]
                    passwd.pop(int(i))
                    passwd.append(a)
                except IndexError:
                    pass
    else:
        raise ValueError('Есть нечитаемые символы!!!')

    for i in passwd:
        result += c_h[abs(c_h.find(i) - len(c_h)) - 1]

    return result
