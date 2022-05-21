#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Filename : error
    Date: 21.12.2018 07:18
    Project: pyRMA
    AUTHOR : Sergey Utkin
    
    Copyright 2018 Sergey Utkin utkins01@gmail.com

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


class QueryError(Exception):
    def __init__(self, desc):
        self.desc = desc

    def __repr__(self):
        return self.desc


class WTF(Exception):
    def __init__(self, desc):
        self.desc = desc

    def __repr__(self):
        return self.desc

class ErrorConnectionJump(Exception):
    def __init__(self, desc):
        self.desc = desc

    def __repr__(self):
        return self.desc
