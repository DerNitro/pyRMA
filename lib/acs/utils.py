import os
import ipaddress


def check_license(lic):
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


def password(passwd, magic, action):
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
