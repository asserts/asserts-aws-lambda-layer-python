import os

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, ProcessCollector, generate_latest


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class LambdaMetrics(metaclass=Singleton):
    a_labelNames = ['asserts_source', 'function_name', 'instance', 'job', 'namespace', 'asserts_site',
                    'asserts_env', 'version']

    def __init__(self):
        self.registry = CollectorRegistry()
        self.process_registry = CollectorRegistry()
        self.process = ProcessCollector(registry=self.process_registry)
        self.up = Gauge('up', 'Heartbeat metric', labelnames=self.a_labelNames, registry=self.registry)
        self.invocations = Counter('aws_lambda_invocations_total', 'AWS Lambda Invocations Count',
                                   labelnames=self.a_labelNames, registry=self.registry)
        self.errors = Counter('aws_lambda_errors_total', 'AWS Lambda Errors Count', labelnames=self.a_labelNames,
                              registry=self.registry)
        self.latency = Histogram('aws_lambda_duration_seconds', 'AWS Lambda Duration Histogram',
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
        self.namespace = 'AWS-Lambda'
        self.asserts_source = 'prom-client'
        self.instance = os.uname()[1]

        self.function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        self.job = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        self.version = os.environ.get('AWS_LAMBDA_FUNCTION_VERSION')
        if os.environ.get('ASSERTS_ENVIRONMENT', ''):
            self.asserts_env = os.environ.get('ASSERTS_ENVIRONMENT')
        else:
            self.asserts_env = ''

        if os.environ.get('ASSERTS_SITE', ''):
            self.asserts_site = os.environ.get('ASSERTS_SITE')
        else:
            self.asserts_site = ''

    def recordInvocation(self):
        self.invocations.labels(self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version).inc()

    def recordError(self):
        self.errors.labels(self.asserts_source, self.function_name, self.instance,
                           self.job, self.namespace, self.asserts_site, self.asserts_env,
                           self.version).inc()

    def recordLatency(self, latency: float):
        self.latency.labels(self.asserts_source, self.function_name, self.instance,
                            self.job, self.namespace, self.asserts_site, self.asserts_env,
                            self.version).observe(latency)

    def updateProcessMetrics(self):
        self.virtual_mem.labels(self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version).set(
            self.process_registry.get_sample_value('process_virtual_memory_bytes'))
        self.res_mem.labels(self.asserts_source, self.function_name, self.instance,
                            self.job, self.namespace, self.asserts_site, self.asserts_env,
                            self.version).set(self.process_registry.get_sample_value('process_resident_memory_bytes'))
        self.start_time.labels(self.asserts_source, self.function_name, self.instance,
                               self.job, self.namespace, self.asserts_site, self.asserts_env,
                               self.version).set(self.process_registry.get_sample_value('process_start_time_seconds'))
        self.open_fd.labels(self.asserts_source, self.function_name, self.instance,
                            self.job, self.namespace, self.asserts_site, self.asserts_env,
                            self.version).set(self.process_registry.get_sample_value('process_open_fds'))
        self.max_fd.labels(self.asserts_source, self.function_name, self.instance,
                           self.job, self.namespace, self.asserts_site, self.asserts_env,
                           self.version).set(self.process_registry.get_sample_value('process_max_fds'))
        self.cpu_seconds.labels(self.asserts_source, self.function_name, self.instance,
                                self.job, self.namespace, self.asserts_site, self.asserts_env,
                                self.version).inc(self.process_registry.get_sample_value('process_cpu_seconds_total'))

    @property
    def getMetrics(self):
        self.updateProcessMetrics()
        return generate_latest(self.registry)
