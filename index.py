# -*- coding: utf-8 -*-
__version__ = '1.0.0'
__doc__ = '''
    handler oss-putobject event 
'''

import os
import json
import time
import logging
import requests
import traceback

import redis
import pika

"""
Define Hyper Parameters Here
"""
# Http config
INTERNAL_SCHEME = 'http'
HTTP_TIMEOUT = 10
# default retry times
SUPPLIER_ALI = 'ali'
SUPPLIER_TX = 'tx'
SUPPLIER_DX = 'dx'
PATH = "/test"

# log level must be one of : [TRACE, DEBUG, INFO, WARN, ERROR]
__log_level = 'INFO'
__http_timeout = 10
__internal_scheme = INTERNAL_SCHEME
__redis_host, __redis_port, __redis_auth, __redis_timeout = '', 6379, '', 10

__redis_service, __http_sender = None, None
__host = ''
__path = PATH

logging.basicConfig(level=__log_level)

class Logger(object):
    def __init__(self, prefix=''):
        self.__prefix = prefix
        self.logger = logging.getLogger()

    @property
    def prefix(self):
        return self.__prefix

    @prefix.setter
    def prefix(self, s):
        self.__prefix = s

    def debug(self, msg):
        self.logger.debug(self.prefix + " | " + msg)

    def info(self, msg):
        self.logger.info(self.prefix + " | " + msg)

    def warning(self, msg):
        self.logger.warning(self.prefix + " | " + msg)

    def error(self, msg):
        self.logger.error(self.prefix + " | " + msg)


logging.getLogger('pika').setLevel(logging.WARNING)
logger = Logger()

# services
class HttpSender(object):
    def __init__(self, internal_scheme: str, timeout: int, host: str, path: str):
        self.internal_scheme = internal_scheme
        self.timeout = timeout
        self.host = internal_scheme + '://' + host
        self.path = path

    def send_post(self, body: dict, params: dict = None):
        res = requests.post(url=self.host + self.path, json=body, timeout=self.timeout, params=params)
        logger.info("send post request, request url: {}, body: {}, resonse: {}".format(self.host + self.path, body, res.text))

class RedisService(object):
    def __init__(self, host: str, port: int = 6379, password: str = '', timeout: int = 10):
        self.__host = host
        self.__port = port
        self.__password = password
        self.__timeout = timeout
        self.__client = redis.StrictRedis(
            host=host, port=port, password=password, socket_connect_timeout=timeout, socket_timeout=timeout)

    def operate_redis(self, key: str):
        self.__client.get(key)
        logger.info("redis command execute success.")

class UploadHandler(object):
    def __init__(
            self, redis_service: RedisService, http_sender: HttpSender):
        self.redis_service = redis_service
        self.http_sender = http_sender

    def handle_upload_event(self, param: dict):
        self.redis_service.operate_redis("key")
        self.http_sender.send_post(param)

def read_environ():
    """
    get environment parameter
    """
    global __log_level, __internal_scheme, \
        __redis_host, __redis_port, __redis_auth, __redis_timeout, __host, __path
    __internal_scheme = 'https' if os.environ.get('INTERNAL_SCHEME') is not None and os.environ.get(
        'INTERNAL_SCHEME').lower() == 'https' else 'http'
    # redis
    __redis_host, __redis_auth = \
        os.environ.get('REDIS_HOST'), os.environ.get('REDIS_AUTH')
    if 'REDIS_PORT' in os.environ.keys() and os.environ.get('REDIS_PORT').isdigit():
        __redis_port = int(os.environ.get('REDIS_PORT'))
    if 'REDIS_TIMEOUT' in os.environ.keys() and os.environ.get('REDIS_TIMEOUT').isdigit():
        __redis_timeout = int(os.environ.get('REDIS_TIMEOUT'))
    __host = os.environ.get('HOST')
    __path = os.environ.get('URL_PATH')

# if you open the initializer feature, please implement the initializer function, as below
def initializer(context, supplier=None):
    global __redis_service, __http_sender, __oss_helper, logger
    logger = Logger('initialize')
    read_environ()
    __redis_service = RedisService(__redis_host, __redis_port, __redis_auth, __redis_timeout)
    __http_sender = HttpSender(__internal_scheme, __http_timeout, __host, __path)

def initializer_for_dx(context):
    initializer(context, supplier=SUPPLIER_DX)

def main(evt: dict, supplier=SUPPLIER_ALI, creds=None):
    param = dict()
    param['region'] = evt['awsRegion']
    param['bucketName'] = evt['s3']['bucket']['name']
    param['key'] = evt['s3']['object']['key']
    param['size'] = evt['s3']['object']['size']
    param['url'] = 'http://10.95.145.8:7480/{}/{}'.format( param['bucketName'], param['key'])
    metadata = evt['s3']['object']['metadata']
    metadata_dict = dict()
    for i in range(len(metadata)):
        metadata_dict[metadata[i]['key']] = metadata[i]['val']
    param['metaData'] = metadata_dict
    upload_handler = UploadHandler(__redis_service, __http_sender)
    return upload_handler.handle_upload_event(param)

def handler_for_dx(event, context):
    global logger
    logger = Logger('handler')
    #initializer_for_dx(context)
    try:
        evt = json.loads(event)
        main(evt['Records'][0], SUPPLIER_DX)
    except BaseException as e:
        logger.error('handler catch exception from main: {}'.format(traceback.format_exc()))
    return 'end'
