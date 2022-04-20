import time, threading
import http.client
import os, ssl
from base64 import b64encode
import logging

from asserts_pylambda.LambdaMetrics import LambdaMetrics
from asserts_pylambda.AssertsUtils import islayer_disabled

logger = logging.getLogger()

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RepeatedTimer(object, metaclass=Singleton):
    def __init__(self, interval):
        self.layer_disabled = islayer_disabled()
        if self.layer_disabled:
            return
        self.metrics = LambdaMetrics()
        self.hostname = os.environ.get('ASSERTS_METRICSTORE_HOST')
        self.port = os.environ.get('ASSERTS_METRICSTORE_PORT')
        self.tenantname = os.environ.get('ASSERTS_TENANT_NAME')
        self.password = os.environ.get('ASSERTS_PASSWORD')

        if self.hostname is not None:
            host_path = self.gethost(self.hostname)
            self.metrichost = host_path[0]
            self.metricpath = '/' + host_path[1]

        if self.port is None:
            self.port = 443

        self._timer = None
        self.interval = interval
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.publishdata()

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def gethost(self, url):
        store_url = str(url)
        split_data = store_url.split('//', 2)
        if len(split_data) == 2:
            return split_data[1].split('/', 1)
        else:
            return split_data[0].split('/', 1)

    def publishdata(self):
        if self.layer_disabled:
            return
        if self.metrichost is not None:
            logger.info("PublishMetrics data")
            if self.port is 443:
                conn = http.client.HTTPSConnection(self.metrichost)
            else:
                conn = http.client.HTTPConnection(self.metrichost, self.port)

            path = self.metricpath

            headers = {'Content-type': 'text/plain'}
            if self.password is not None:
                headers['Authorization'] = "Basic {}".format(
                    b64encode(bytes(f"{self.tenantname}:{self.password}", "utf-8")).decode("ascii"))

            body = self.metrics.getMetrics
            conn.request('POST', path, body, headers)
            response = conn.getresponse()
            code = response.getcode()
            if code != http.HTTPStatus.OK:
                logger.info('Unable to send metrics %d', code)
            else:
                logger.info('Metrics Published successfully')
