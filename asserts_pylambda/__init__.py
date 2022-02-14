import asserts_pylambda
import logging
import os
from asserts_pylambda.PublishMetrics import RepeatedTimer
from asserts_pylambda.AssertsLambdaPython import AssertsLambdaPython

logger = logging.getLogger()
valid = {'true': True, 'false': False, }

layer_disabled = False
value = os.environ.get('ASSERTS_LAYER_DISABLED')
if value is not None:
    lower_value = value.lower()
    if lower_value in valid:
        layer_disabled = valid[lower_value]

if layer_disabled:
    logger.info("AWS Lambda Python Function instrumentation is disabled.")
else:
    logger.info("Instrumenting AWS Lambda Python.")
    asserts = AssertsLambdaPython()
    rt = RepeatedTimer(15)

