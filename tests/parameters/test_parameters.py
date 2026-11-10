import configparser
from unittest.mock import patch

import pytest

from pyrmalib import parameters


def test_check_config_valid():
    cfg = configparser.ConfigParser()
    cfg.add_section('Main')
    cfg.add_section('DataBase')
    assert parameters.check_config(cfg) is True


def test_check_config_missing_section():
    cfg = configparser.ConfigParser()
    with pytest.raises(parameters.CheckConfigError):
        parameters.check_config(cfg)


@pytest.fixture
def mock_config_file(tmp_path):
    conf_file = tmp_path / "pyrma.conf"
    conf_content = """
[Main]
data_dir = /data
app_ip_address = 127.0.0.1
auto_extension = 1
extension_days = 21
check_source_ip = 0
forward_tcp_port_range = 10000:15000
file_env = filerec
path_env = filerecord
modules = /etc/pyrma/mod.d
log_level = INFO
app_dir = /app

[DataBase]
provider = postgresql
dbhost = localhost
dbport = 5432
dbuser = acs
dbpass = acs
dbname = acs

[Email]
domain_name = localhost
type = smtp
host = localhost
port = 25
from = acs@localhost

[IPMI]
local_ips = 127.0.0.1

[Web]
ip = 127.0.0.1
port = 8080
live_time = 60
log_level = INFO
template = index.html

[Firewall]
firewall_forward_table = filter
tcp_capture_folder = /capture
tcp_forward_interface = eth0

[FileTransfer]
file_transfer_folder = /ft
file_transfer_backup_folder = /ft_backup
"""
    conf_file.write_text(conf_content)
    return str(conf_file)


@patch('pyrmalib.parameters.log.Log')
@patch('os.path.isfile', return_value=True)
@patch('os.access', return_value=True)
def test_all_parameter_classes(mock_access, mock_isfile, mock_log_cls, mock_config_file):
    with patch('pyrmalib.parameters.pathConfigFile', mock_config_file):
        p = parameters.Parameters()
        assert p.dbase == 'postgresql'
        assert p.check_user() is False
        assert repr(p) is not None

        ap = parameters.AppParameters()
        assert ap.app_folder == '/app'
        assert repr(ap) is not None

        wp = parameters.WebParameters()
        assert wp.port == '8080'
        assert repr(wp) is not None

        api_p = parameters.APIParameters()
        assert api_p.log is not None
        assert repr(api_p) is not None

        fp = parameters.FirewallParameters()
        assert fp.firewall_forward_table == 'filter'
        assert repr(fp) is not None

        ftp = parameters.FileTransfer()
        assert ftp.file_transfer_folder == '/ft'
        assert repr(ftp) is not None
