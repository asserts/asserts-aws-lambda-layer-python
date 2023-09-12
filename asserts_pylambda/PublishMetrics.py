import time, threading
import http.client
import os
from base64 import b64encode
import logging
import requests

from asserts_pylambda.LambdaMetrics import LambdaMetrics
from asserts_pylambda.AssertsUtils import is_layer_disabled

logger = logging.getLogger()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RepeatedTimer(object, metaclass=Singleton):
    def __init__(self, interval):
        self.layer_disabled = is_layer_disabled()
        if self.layer_disabled:
            return
        self.metrics = LambdaMetrics()
        self.hostname = os.environ.get('ASSERTS_METRIC_ENDPOINT')
        self.tenantname = os.environ.get('ASSERTS_TENANT_NAME')
        self.password = os.environ.get('ASSERTS_PASSWORD')

        self._timer = None
        self.interval = interval
        self.is_running = False
        self.next_call = time.time()

        # Publish metrics once to capture cold start before request processing
        self.publish_metrics()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.publish_metrics()

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def publish_metrics(self):
        if self.layer_disabled:
            return
        if self.hostname is not None:
            logger.info("PublishMetrics data")
            body = self.metrics.get_metrics
            headers = {'Content-type': 'text/plain'}
            if self.password is not None:
                headers['Authorization'] = "Basic {}".format(
                    b64encode(bytes(f"{self.tenantname}:{self.password}", "utf-8")).decode("ascii"))
            response = requests.post(self.hostname, headers=headers, data=body)
            if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.NO_CONTENT:
                logger.info('Unable to send metrics %d', response.status_code)
            else:
                logger.info('Metrics Published successfully')

        # Update cold start status
        if self.metrics.is_cold_start is True:
            self.metrics.is_cold_start = False

