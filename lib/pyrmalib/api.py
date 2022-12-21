# -*- coding: utf-8 -*-
# encoding: utf-8
"""
       Copyright 2022 Sergey Utkin utkins01@gmail.com

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

from flask_restful import Resource, request
from flask_httpauth import HTTPBasicAuth

import pam
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from pyrmalib import parameters, schema, applib, utils, error

auth = HTTPBasicAuth()

apiParameters = parameters.APIParameters()
apiParameters.engine = create_engine(
    '{0}://{1}:{2}@{3}:{4}/{5}'.format(
        apiParameters.dbase,
        apiParameters.dbase_param["user"],
        apiParameters.dbase_param["password"],
        apiParameters.dbase_param["host"],
        apiParameters.dbase_param["port"],
        apiParameters.dbase_param["database"]
    )
)

@auth.verify_password
def verify_password(username, password):
    apiParameters.log.info(f'verify_password: {username} from {request.remote_addr}')
    if not pam.authenticate(username=username, password=password):
        return False
    
    with schema.db_select(apiParameters.engine) as db:
        try:
            user = db.query(schema.User).filter(schema.User.login == username).one()
        except NoResultFound:
            return False
        except MultipleResultsFound:
            return False
    if not user.admin:
        return False
    if not utils.check_ip(request.remote_addr, user.ip) and apiParameters.check_source_ip == '1':
        return False

    apiParameters.user_info = user
    return True


@auth.error_handler
def unauthorized():
    apiParameters.log.warning('Unauthorized access')
    return {'message': 'Unauthorized access'}, 403


class Monitoring(Resource):
    decorators = [auth.login_required]

    def get(self):
        apiParameters.log.info('/api/monitor get request')
        
        return {
            "active_connection": len(applib.get_connections(apiParameters, active=True)),
            "new_user": len(applib.get_new_user(apiParameters)),
            "access_request": len(applib.get_access_request(apiParameters))
            }, 200


class HostUpload(Resource):
    decorators = [auth.login_required]

    def post(self):
        upload_file = request.files['file']
        _, upload_file_path = tempfile.mkstemp()
        
        apiParameters.log.debug(f'tempfile: {upload_file_path}')
        apiParameters.log.info(f'/api/host/upload post request: {upload_file.filename}')
        upload_file.save(upload_file_path)

        try:
            created_host, updated_host, skipped_host = applib.add_hosts_file(apiParameters, upload_file_path)
        except error.WTF as e:
            return {'status': 'error', 'error': str(e)}, 500
        finally:
            os.remove(upload_file_path)
        
        return {
            'status': 'success', 
            'created host': created_host, 
            'updated host': updated_host, 
            'skipped host': skipped_host
            }, 200
