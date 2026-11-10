# План доработок проекта pyRMA (TODO)

## 1. Качество кода и линтинг (Ruff)
- [x] Очистить неиспользуемые импорты в модулях (`bin/firewall.py`, `lib/pyrmalib/template.py` и др.).
- [x] Исправить несортированные блоки импортов в соответствии с правилами сортировки (I001).
- [x] Заменить устаревшие вызовы `.format()` на современные f-строки (UP032) для повышения читаемости и производительности.
- [x] Удалить лишние пробелы в пустых строках (W293) и trailing whitespace (W291).
- [x] Заменить некорректные экранирования и синтаксические конструкции, отмеченные линтером (включая устранение голых except и неоднозначных имен переменных).

## 2. Архитектура и структура проекта
- [ ] Проверить и унифицировать импорты библиотеки `pyrmalib` из скриптов в каталоге `bin/`.
- [ ] Рассмотреть возможность добавления `pyproject.toml` для настройки сборки пакета и инструментов (ruff, pytest, coverage) в едином месте.
- [ ] Убедиться, что пути к конфигурационным файлам и логам корректно параметризованы во всех демонах (`firewall.py`, `web.py`, `ft.py`).

## 3. Тестирование и CI/CD (Список задач на покрытие unit-тестами)
Текущее покрытие unit-тестами имеется только для двух функций в `applib.py` (`check_access_request`, `get_user_access`). Ниже представлен подробный список всех функций, методов и классов библиотеки `pyrmalib`, требующих написания unit-тестов.

### 3.1. `src/pyrmalib/access.py`
- [x] Класс `Access` (методы `__init__`, `__repr__`, `change`, `get`, `get_int`)
- [x] Класс `UserAccess` (метод `__init__`)
- [x] Класс `ConnectionAccess` (метод `__init__`)
- [x] Функция `get_user_access`
- [x] Функция `check_access`
- [x] Функция `users_access_list`
- [x] Функция `request_access`
- [x] Функция `access_request`
- [x] Функция `deny_request`

### 3.2. `src/pyrmalib/api.py`
- [x] Функция `verify_password`
- [x] Функция `unauthorized`
- [x] Класс `Monitoring` (метод `get`)
- [x] Класс `HostUpload` (метод `post`)

### 3.3. `src/pyrmalib/applib.py`
- [ ] Функция `authorization`
- [ ] Функция `login_access`
- [ ] Функция `check_ip_net`
- [ ] Функция `change_ipmi`
- [ ] Функция `check_host`
- [ ] Функция `get_access_list`
- [ ] Функция `get_access_request`
- [x] Функция `check_access_request` (покрыта тестом)
- [ ] Функция `get_stdin_command`
- [ ] Функция `get_connection`
- [ ] Функция `get_file_transfer`
- [ ] Функция `get_session`
- [ ] Функция `get_connections`
- [ ] Функция `get_content_host`
- [ ] Функция `get_admin_content_dashboard`
- [ ] Функция `get_user_content_dashboard`
- [ ] Функция `get_host`
- [ ] Функция `get_host_list`
- [ ] Функция `get_service`
- [ ] Функция `get_connection_type`
- [ ] Функция `get_file_transfer_type`
- [ ] Функция `get_ilo_type`
- [ ] Функция `get_folders`
- [ ] Функция `get_service_type`
- [ ] Функция `get_local_port`
- [ ] Функция `get_jump_hosts`
- [ ] Функция `get_jump_host`
- [ ] Функция `get_group`
- [ ] Функция `get_group_user`
- [ ] Функция `get_group_host`
- [ ] Функция `get_group_list`
- [ ] Функция `get_users`
- [ ] Функция `get_parameters`
- [ ] Функция `get_user`
- [ ] Функция `get_admin_users`
- [ ] Функция `get_user_group`
- [x] Функция `get_user_access` (покрыта тестом)
- [ ] Функция `get_group_access`
- [ ] Функция `get_user_permission`
- [ ] Функция `get_group_permission`
- [ ] Функция `get_host_group`
- [ ] Функция `get_parent_host`
- [ ] Функция `get_action`
- [ ] Функция `get_prefix`
- [ ] Функция `get_new_user`
- [ ] Функция `add_user_group`
- [ ] Функция `add_host_group`
- [ ] Функция `add_prefix`
- [ ] Функция `add_ipmi`
- [ ] Функция `set_user_permission`
- [ ] Функция `set_group_permission`
- [ ] Функция `set_user_prefix`
- [ ] Функция `set_parameters`
- [ ] Функция `set_file_transfer`
- [ ] Функция `search`
- [ ] Функция `user_info`
- [ ] Функция `user_edit`
- [ ] Функция `user_disable`
- [ ] Функция `user_admin_disable`
- [ ] Функция `restore_deny_password`
- [ ] Функция `user_registration`
- [ ] Функция `add_folder`
- [ ] Функция `add_host`
- [ ] Функция `update_host`
- [ ] Функция `add_service`
- [ ] Функция `add_service_type`
- [ ] Функция `add_hosts_file`
- [ ] Функция `add_jump`
- [ ] Функция `add_group`
- [ ] Функция `add_access`
- [ ] Функция `edit_folder`
- [ ] Функция `edit_host`
- [ ] Функция `delete_folder`
- [ ] Функция `delete_host`
- [ ] Функция `del_group`
- [ ] Функция `del_access`
- [ ] Функция `del_group_user`
- [ ] Функция `del_group_host`
- [ ] Функция `del_service`
- [ ] Функция `del_prefix`
- [ ] Функция `del_service_type`
- [ ] Функция `del_ipmi`
- [ ] Функция `clear_jump`
- [ ] Функция `close_dead_session`
- [ ] Функция `check_worktime`
- [ ] Функция `get_password`
- [ ] Функция `save_password`
- [ ] Функция `tcp_forward_connection`
- [ ] Функция `get_tcp_forward_connection`
- [ ] Функция `del_tcp_forward_connection`
- [ ] Функция `tcp_forward_connection_is_active`
- [ ] Функция `add_capture_traffic`
- [ ] Функция `get_folder_path`
- [ ] Функция `get_folder_id`

### 3.4. `src/pyrmalib/connection.py`
- [ ] Класс `SSH` (методы `__init__`, `connection`)
- [ ] Класс `SFTP` (методы `__init__`, `connection`)
- [ ] Класс `TELNET` (методы `__init__`, `connection`)
- [ ] Класс `SERVICE` (методы `__init__`, `connection`)
- [ ] Класс `IPMI` (методы `__init__`, `run`, `close`, `connection`, `firewall`)

### 3.5. `src/pyrmalib/error.py`
- [ ] Классы исключений (`QueryError`, `HostDuplicatedResult`, `WTF`, `ErrorConnectionJump`, `ErrorGetListFiles`, `ErrorConnectionIPMI`, `InsertError`, `HandleSigTerm`, `TerminalResize`)

### 3.6. `src/pyrmalib/forms.py`
- [ ] Функция `ip_net_check`
- [ ] Функция `port_list_check`
- [ ] Классы форм WTForms (`Login`, `EditFolder`, `EditHost`, `AddServiceHost`, `AddServiceHostAdmin`, `JumpHost`, `AddGroup`, `ChangePermission`, `AddUserGroup`, `AddHostGroup`, `ResetPassword`, `Search`, `ShowLog`, `ChangePrefix`, `AddAccess`, `DelButton`, `Parameters`, `AddPrefix`, `IPMI`, `AddService`, `Access`, `ConnectionFilter`, `User`)

### 3.7. `src/pyrmalib/interface.py`
- [ ] Функция `echo_form`
- [ ] Классы интерфейса (`MultiLineEditableBoxed`, `RecordList`, `HostListDisplay`, `Find`, `AccessRequest`, `Filter`, `ConnectionForm`, `InformationForm`, `ErrorForm`, `Interface`)

### 3.8. `src/pyrmalib/log.py`
- [x] Класс `Log` (методы `__init__`, `error`, `info`, `warning`, `debug`, `critical`, `exception`)

### 3.9. `src/pyrmalib/mail.py`
- [x] Класс `Mail` (методы `__init__`, `send`, `__repr__`)
- [x] Функция `send_mail`

### 3.10. `src/pyrmalib/modules.py`
- [x] Классы `Modules` и `ConnectionModules` (методы `__init__`, `run`, `close`, `connection`, `firewall`)

### 3.11. `src/pyrmalib/parameters.py`
- [x] Функция `check_config`
- [x] Классы параметров (`CheckConfigError`, `Parameters`, `AppParameters`, `WebParameters`, `APIParameters`, `FirewallParameters`, `FileTransfer`)

### 3.12. `src/pyrmalib/rec_file.py`
- [ ] Класс `RecFile` (методы `__init__`, `stdin_to_line`, `__repr__`)

### 3.13. `src/pyrmalib/schema.py`
- [ ] Функция `db_select`
- [ ] Функция `db_edit`
- [ ] Модели БД SQLAlchemy (`User`, `Action`, `ActionType`, `RequestAccess`, `Host`, `IPMIType`, `Service`, `ServiceType`, `JumpHost`, `Connection`, `Session`, `ConnectionType`, `FileTransferType`, `Prefix`, `Group`, `GroupHost`, `GroupUser`, `Permission`, `AccessList`, `PasswordList`, `ForwardTCP`, `FileTransfer`, `CaptureTraffic`)

### 3.14. `src/pyrmalib/template.py`
- [ ] Функция `request_access`
- [ ] Функция `deny_request`
- [ ] Функция `access_request`
- [ ] Функция `help_main_form`
- [ ] Функция `help_ft_form`
- [ ] Функция `registration_user`

### 3.15. `src/pyrmalib/utils.py`
- [ ] Функция `get_app_parameters`
- [ ] Функция `check_ip`
- [ ] Функция `valid_ip`
- [ ] Функция `valid_net`
- [ ] Функция `check_ip_network`
- [ ] Функция `password`
- [ ] Функция `date_to_datetime`
- [ ] Функция `md5`

- [x] Добавить автоматический запуск линтера (`ruff check .`) и тестов в пайплайн или локальные хуки git (pre-commit).

## 4. Документация
- [ ] Актуализировать инструкции по установке и запуску в `README.rst` с учетом текущей версии Python (3.12+) и окружения `pyenv`.
