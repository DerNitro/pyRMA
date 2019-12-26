
=====
pyRMA
=====
**pyRMA** - Система контроля удаленного доступа к серверному и сетевому
оборудованию по протоколам SSH и TELNET.

Установка
=========
Требования
----------
1. Операционная система: CentOS7
2. CPU: 2
3. RAM: 1GB
4. HDD: 6GB
5. Python 3.6
6. PostgreSQL 9


Установка python
----------------
::

    [root@pyrma ~]# yum install python3 gcc python-devel python3-devel
    [root@pyrma ~]# pip3 install flask
    [root@pyrma ~]# pip3 install flask_wtf
    [root@pyrma ~]# pip3 install sqlalchemy
    [root@pyrma ~]# pip3 install psycopg2
    [root@pyrma ~]# pip3 install wtforms
    [root@pyrma ~]# pip3 install psutils


Установка PostgreSQL
--------------------
::

    [root@pyrma ~]# yum install postgresql-server postgresql-devel
    [root@pyrma ~]# postgresql-setup
    [root@pyrma ~]# systemctl start postgresql
    [root@pyrma ~]# sudo -u postgres psql*
    postgres=# create database pyrma;
    postgres=# create user pyrma with encrypted password 'pyrma';
    postgres=# grant all privileges on database pyrma to pyrma;

Меняем строки в /var/lib/pgsql/data/pg_hba.conf
::

    # IPv4 local connections:
    host    all             all             127.0.0.1/32            md5
    # IPv6 local connections:
    host    all             all             ::1/128                 md5


Установка pyRMA
---------------
Устанавливаем pyRMA в /opt

::

    [root@pyrma ~]# ln -s /opt/pyRMA/etc/pyrma /etc/pyrma
    [root@pyrma ~]# ln -s /opt/pyRMA/lib/pyrmalib /usr/lib64/python3.6/pyrmalib
    [root@pyrma ~]# mkdir -p /var/log/pyRMA/ /data/pyRMA
    [root@pyrma ~]# cd /opt/pyRMA/lib/pyrmalib/
    [root@pyrma pyrmalib]# python3 schema.py install


Запуск
======
Web Интерфейс
-------------
::

    [root@pyrma ~]# python3 /opt/pyRMA/bin/web.py

* Логин:  admin
* Пароль: admin

Инструкция пользователя
=======================
Особености
----------
* Доступ и управление хостами осуществляется на уровне групп и списка доступов.