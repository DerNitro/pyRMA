
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


Отключаем SELINUX
-----------------
::

    [root@pyrma ~]# setenforce Permissive

Выставляем в /etc/selinux/config, параметр SELINUX в disable
::

    [root@pyrma selinux]# cat /etc/selinux/config

    # This file controls the state of SELinux on the system.
    # SELINUX= can take one of these three values:
    #     enforcing - SELinux security policy is enforced.
    #     permissive - SELinux prints warnings instead of enforcing.
    #     disabled - No SELinux policy is loaded.
    SELINUX=disable
    # SELINUXTYPE= can take one of three values:
    #     targeted - Targeted processes are protected,
    #     minimum - Modification of targeted policy. Only selected processes are protected.
    #     mls - Multi Level Security protection.
    SELINUXTYPE=targeted

Установка PostgreSQL
--------------------
::

    [root@pyrma ~]# yum install postgresql-server postgresql-devel
    [root@pyrma ~]# postgresql-setup initdb
    [root@pyrma ~]# systemctl start postgresql
    [root@pyrma ~]# systemctl enable postgresql
    [root@pyrma ~]# sudo -u postgres psql
    postgres=# create database acs;
    postgres=# create user acs with encrypted password 'acs';
    postgres=# grant all privileges on database acs to acs;

Меняем строки в /var/lib/pgsql/data/pg_hba.conf
::

    # IPv4 local connections:
    host    all             all             127.0.0.1/32            md5
    # IPv6 local connections:
    host    all             all             ::1/128                 md5

Перезапускаем PostgreSQL
::

    systemctl restart postgresql

Установка python
----------------
::

    [root@pyrma ~]# yum install python3 gcc gcc-c++ python-devel python3-devel libgcrypt-devel autoconf automake git xmlto libtool
    [root@pyrma ~]# pip3 install flask
    [root@pyrma ~]# pip3 install npyscreen
    [root@pyrma ~]# pip3 install flask_wtf
    [root@pyrma ~]# pip3 install sqlalchemy
    [root@pyrma ~]# pip3 install psycopg2
    [root@pyrma ~]# pip3 install wtforms
    [root@pyrma ~]# pip3 install psutil


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
    [root@pyrma ~]# cp /opt/pyRMA/etc/nss-pgsql* /etc/
    [root@pyrma ~]# chmod 600 /etc/nss-pgsql-root.conf
    [root@pyrma ~]# chown root:root /etc/nss-pgsql-root.conf
    [root@pyrma ~]# cd /opt/pyRMA/lib/pyrmalib/
    [root@pyrma pyrmalib]# python3 schema.py install


Установка libnss-pgsql
----------------------
::

    [root@pyrma ~]# yum install xmlto libtool
    [root@pyrma ~]# git clone https://github.com/jandd/libnss-pgsql.git
    [root@pyrma ~]# cd libnss-pgsql/

Для начала требуется внести изменения в src/backend.c, заменить #include <postgres/libpq-fe.h> на #include <libpq-fe.h>
::

    [root@pyrma libnss-pgsql]# ./configure --libdir=/usr/lib64 --sysconfdir=/etc
    [root@pyrma libnss-pgsql]# make
    [root@pyrma libnss-pgsql]# make install


Добавляем в файл /etc/nsswitch.conf значение pgsql
::

    passwd:     files sss pgsql
    shadow:     files sss pgsql
    group:      files sss pgsql

Установка pam-pgsql
-------------------
::

    [root@pyrma ~]# yum install libgcrypt-devel autoconf automake libtool pam-devel
    [root@pyrma ~]# git clone https://github.com/pam-pgsql/pam-pgsql.git
    [root@pyrma ~]# cd pam-pgsql/
    [root@pyrma pam-pgsql]# ./autogen.sh
    [root@pyrma pam-pgsql]# ./configure
    [root@pyrma pam-pgsql]# make
    [root@pyrma pam-pgsql]# make install
    [root@pyrma pam-pgsql]# cp /opt/pyRMA/etc/pam_pgsql.conf /etc/pam_pgsql.conf
    [root@pyrma pam-pgsql]# ln -s /usr/local/lib/security/pam_pgsql.so /usr/lib64/security/pam_pgsql.so

Настройка /etc/pam.d/sshd

Добавляем строки:
    * auth       sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf
    * account    sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf
    * password   sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf

::

    [root@pyrma pam.d]# cat /etc/pam.d/sshd
    #%PAM-1.0
    auth	   required	pam_sepermit.so
    auth       sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf
    auth       substack     password-auth
    auth       include      postlogin
    # Used with polkit to reauthorize users in remote sessions
    -auth      optional     pam_reauthorize.so prepare
    account    required     pam_nologin.so
    account    sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf
    account    include      password-auth
    password   include      password-auth
    password   sufficient   pam_pgsql.so config_file=/etc/pam_pgsql.conf
    # pam_selinux.so close should be the first session rule
    session    required     pam_selinux.so close
    session    required     pam_loginuid.so
    # pam_selinux.so open should only be followed by sessions to be executed in the user context
    session    required     pam_selinux.so open env_params
    session    required     pam_namespace.so
    session    optional     pam_keyinit.so force revoke
    session    include      password-auth
    session    include      postlogin
    # Used with polkit to reauthorize users in remote sessions
    -session   optional     pam_reauthorize.so prepare


Подготовка к запуску
--------------------
::

    [root@pyrma ~]# chown admin.acs -R /var/log/pyRMA/ /data/pyRMA
    [root@pyrma ~]# chmod 6775 /data/pyRMA /var/log/pyRMA/
    [root@pyrma ~]# ln -s /opt/pyRMA/etc/security/limit.d/acs.conf /etc/security/limit.d/acs.conf

Добавить строку /opt/pyRMA/bin/pyrma.sh в /etc/shells
::

    [root@pyrma ~]# cat /etc/shells
    /bin/sh
    /bin/bash
    /usr/bin/sh
    /usr/bin/bash
    /opt/pyRMA/bin/pyrma.sh

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