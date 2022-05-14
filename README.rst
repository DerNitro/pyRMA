
=====
pyRMA
=====
**pyRMA** - Система контроля удаленного доступа к серверному и сетевому
оборудованию по протоколам SSH и TELNET.

Установка
=========
Требования
----------
* **OS**: Ubuntu 20.04
* **RAM**: 1GB
* **HDD**: 20GB

Подготовка
----------
Заполнить иниентарный файл ansible/inventory.yml

.. code-block::

  pyrma:
    hosts:
      pyrma.vmlocal:  
    vars:
      install_postgresql: yes
      pyrma_database:
        name: 'acs'
        username: 'acs'
        password: 'acs'

**Возможные переменные**:

* **app_user**: локальный пользователь, по умолчанию 'acs'
* **app_user_password**: пароль локального пользователя, по умолчанию 'admin'
* **app_group**: локальная группа, по умолчанию 'acs'
* **app_folder**: директория установки приложения, по умолчанию '/opt/pyRMA'
* **app_data_dir**: директория данных приложения, по умолчанию '/data/pyRMA'
* **app_log_level**: уровень логирования, по умолчанию 'INFO'
* **app_web_ip**: адрес веб интрефеса приложения, по умолчанию '0.0.0.0'
* **app_web_port**: порт веб приложения, по умолчанию '8080'
* **pyrma_database**: Настройки подключения к СУБД PostgreSQL
    * **name**: Имя базы данных, по умолчанию 'acs'
    * **host**: Адрес базы данных, по умолчанию '127.0.0.1'
    * **port**: TCP порт подключения к базе данных, по умолчанию '5432'
    * **username**: Имя пользователя для подключения к базе данных, по умолчанию 'acs'
    * **password**: Пароль пользователя, для подключения к базе данных, по умолчанию 'acs'
* **install_postgresql**: Флаг установки СУБД PostgreSQL, принимает значения yes/no
* **email_domain_name**: доменное имя элекронной почты

Установка
---------
.. code-block::

    python3 -m venv venv
    source venv/bin/activate 
    pip3 install -r requirements.txt --upgrade
    ansible-playbook deploy.yml


Запуск
======
Web Интерфейс
-------------

* Логин:  admin
* Пароль: admin

Firewall
--------

Инструкция пользователя
=======================
