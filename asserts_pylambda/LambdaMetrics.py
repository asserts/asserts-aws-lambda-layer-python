import os
import sys

from prometheus_client import Counter, Gauge, CollectorRegistry, ProcessCollector, PlatformCollector, generate_latest


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LambdaMetrics(metaclass=Singleton):
    a_labelNames = ['account_id', 'region', 'asserts_source', 'function_name', 'instance', 'job',
                    'namespace', 'asserts_site',
                    'asserts_env', 'version', 'runtime', 'layer_version']

    def __init__(self):
        self.registry = CollectorRegistry()
        self.process_registry = CollectorRegistry()
        self.process = ProcessCollector(registry=self.process_registry)
        self.platform = PlatformCollector(registry=self.process_registry)
        self.is_cold_start = True
        self.runtime = 'python'
        self.cold_start = Gauge('aws_lambda_cold_start', 'Cold Start indicator',
                                 labelnames=self.a_labelNames, registry=self.registry)
        self.virtual_mem = Gauge('process_virtual_memory_bytes', 'Virtual memory size in bytes',
                                 labelnames=self.a_labelNames, registry=self.registry)
        self.res_mem = Gauge('process_resident_memory_bytes', 'Resident memory size in bytes',
                             labelnames=self.a_labelNames, registry=self.registry)
        self.start_time = Gauge('process_start_time_seconds', 'Start time of the process since unix epoch in seconds',
                                labelnames=self.a_labelNames, registry=self.registry)
        self.cpu_seconds = Counter('process_cpu_seconds_total', 'Total user and system CPU time spent in seconds',
                                   labelnames=self.a_labelNames, registry=self.registry)
        self.open_fd = Gauge('process_open_fds', 'Number of open file descriptors', labelnames=self.a_labelNames,
                             registry=self.registry)
        self.max_fd = Gauge('process_max_fds', 'Maximum number of open file descriptors', labelnames=self.a_labelNames,
                            registry=self.registry)
        self.namespace = 'AWS/Lambda'
        self.asserts_source = 'prom-client'
        self.instance = os.uname()[1]
        self.runtime_version = sys.version
        self.layer_version = '__layer_version__'

        self.function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        self.job = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        self.version = os.environ.get('AWS_LAMBDA_FUNCTION_VERSION')
        self.account_id = os.environ.get('ACCOUNT_ID')
        self.region = os.environ.get('AWS_REGION')
        if os.environ.get('ASSERTS_ENVIRONMENT') is not None:
            self.asserts_env = os.environ.get('ASSERTS_ENVIRONMENT')
        else:
            self.asserts_env = self.account_id

        if os.environ.get('ASSERTS_SITE') is not None:
            self.asserts_site = os.environ.get('ASSERTS_SITE')
        else:
            self.asserts_site = self.region

    def update_process_metrics(self):
        if self.is_cold_start is True:
            self.cold_start.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version, self.runtime, self.layer_version).set(1)
        else:
            self.cold_start.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version, self.runtime, self.layer_version).set(0)

        self.virtual_mem.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version, self.runtime, self.layer_version).set(
            self.process_registry.get_sample_value('process_virtual_memory_bytes'))
        self.res_mem.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                            self.job, self.namespace, self.asserts_site, self.asserts_env,
                            self.version, self.runtime, self.layer_version).set(self.process_registry.get_sample_value('process_resident_memory_bytes'))
        self.start_time.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                               self.job, self.namespace, self.asserts_site, self.asserts_env,
                               self.version, self.runtime, self.layer_version).set(self.process_registry.get_sample_value('process_start_time_seconds'))
        self.open_fd.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                            self.job, self.namespace, self.asserts_site, self.asserts_env,
                            self.version, self.runtime, self.layer_version).set(self.process_registry.get_sample_value('process_open_fds'))
        self.max_fd.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                           self.job, self.namespace, self.asserts_site, self.asserts_env,
                           self.version, self.runtime, self.layer_version).set(self.process_registry.get_sample_value('process_max_fds'))
        self.cpu_seconds.labels(self.account_id, self.region, self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version, self.runtime, self.layer_version).inc(self.process_registry.get_sample_value('process_cpu_seconds_total'))


    @property
    def get_metrics(self):
        self.update_process_metrics()
        return generate_latest(self.registry)
