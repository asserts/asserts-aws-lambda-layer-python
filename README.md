# aws-lambda-layer-python

AWS Lambda layer to capture runtime metrics from a Python AWS Lambda function. The layer uses [client_python](https://github.com/prometheus/client_python) to capture the metrics and forwards them to a configured end point through a `https` `POST` method on api `/api/v1/import/prometheus`. The metrics are sent in prometheus text format

# Programmatic instrumentation

If your Lambda code is written in Python, you can import asserts lambda layer as follows

```
import asserts_pylambda
```

In your Lambda Handler code
```
import asserts_pylambda

def lambda_handler(event, context):
    ..your hander code...

```

# Environment variables for forwarding metrics to a prometheus end-point
The following environment variables will have to be defined regardless of whether you use programmatic or automatic instrumentation

|Variable name| Description|
|-------------|------------|
|`ASSERTS_METRIC_ENDPOINT`|An endpoint which can receive the `POST` method call on api `/api/v1/import/prometheus`. This can either be an asserts cloud endpoint or an end point exposed on the EC2 or ECS instance where [Asserts AWS Exporter](https://docs.asserts.ai/user-guide/integrations/aws) is deployed or [Victoria Metrics](https://docs.victoriametrics.com/Single-server-VictoriaMetrics.html#how-to-import-data-in-prometheus-exposition-format) ingestion end point|
|`ASSERTS_TENANT_NAME`|The tenant name in the Asserts Cloud where the metrics will be ingested |
|`ASSERTS_PASSWORD`|If the endpoint supports and expects Basic authorization the credentials can be configured here |
|`ASSERTS_LAYER_DISABLED`| If set to `true`, the layer will be disabled|

# Exported Metrics

The process metrics collected by [client_python](https://github.com/prometheus/client_python) are automatically exported.


# Add layer to Lambda function
To add the layer to your function `Sample-Function`, copy the `deployment/sample-config.yml` as `config.yml`. Specify
the function name and layer ARN and other environment properties and run the `manage_asserts_layer` script


```
# Supported operations are 'add-layer', 'update-version', 'update-env-variables', 'disable-layer', 'enable-layer', 'remove-layer'
operation: add-layer

# Layer arn needs to be specified for 'add' or 'update-version' operations
layer_arn: arn:aws:lambda:us-west-2:689200961921:layer:asserts-aws-lambda-layer-python:8

# Metric Ingestion endpoint
ASSERTS_METRIC_ENDPOINT: https://chief.tsdb.dev.asserts.ai/api/v1/import/prometheus

# ASSERTS_TENANT_NAME and ASSERTS_PASSWORD is optional
ASSERTS_TENANT_NAME: chief
ASSERTS_PASSWORD: wrong

# Functions can be specified either through a regex pattern or through a list of function names
# function_name_pattern: Sample.+
function_names:
  - function_py
```

```
python manage_asserts_layer.py
```
