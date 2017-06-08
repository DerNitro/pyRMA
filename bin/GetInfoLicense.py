#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding: utf-8

import os
import socket
import platform
import hashlib

host_id = os.popen("hostid").read().strip()
host_name = socket.gethostname()
platform = platform.system()

print(hashlib.md5(host_id.encode('utf-8')).hexdigest(), host_name, platform)
