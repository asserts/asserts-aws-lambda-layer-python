import time, threading
import http.client
import os, ssl
from base64 import b64encode
import logging

from asserts_pylambda.LambdaMetrics import LambdaMetrics

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

class RepeatedTimer(object,metaclass=Singleton):
  def __init__(self, interval):
    self.metrics = LambdaMetrics()
    self.hostname = os.environ.get('ASSERTS_REMOTE_WRITE_URL')
    self.tenantname = os.environ.get('ASSERTS_TENANT_NAME')
    self.password = os.environ.get('ASSERTS_PASSWORD')
    if self.tenantname is not None:
      self.metrics.setTenant(self.tenantname)
    self._timer = None
    self.interval = interval
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.publishData()

  def start(self):
    if not self.is_running:
      logger.info("Starting RepeatedTimer")
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False

  def publishData(self):
    if self.tenantname is not None and self.hostname is not None and self.password is not None:
      logger.info("PublishMetrics data")
      #conn = http.client.HTTPSConnection('chief.tsdb.dev.asserts.ai')
      conn = http.client.HTTPConnection(self.hostname)
      #path = '/api/v1/import/prometheus'
      path = '/metrics/job/prom-push'
      #headers = {'Content-type': 'application/json'}
      headers = {'Content-type': 'text/plain',
                  "Authorization": "Basic {}".format(
                  b64encode(bytes(f"{self.tenantname}:{self.password}", "utf-8")).decode("ascii"))
          }
      body = self.metrics.getMetrics
      conn.request('POST', path, body, headers)
      response = conn.getresponse()
      code = response.getcode()
      if code != http.HTTPStatus.OK:
        logger.info('Unable to send metrics %d',code)
      else:
        logger.info('Metrics Published successfully')