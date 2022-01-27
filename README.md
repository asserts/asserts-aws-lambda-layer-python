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
|`ASSERTS_REMOTE_WRITE_URL`|An endpoint which can receive the `POST` method call on api `/api/v1/import/prometheus`. This can either be an asserts cloud endpoint or an end point exposed on the EC2 or ECS instance where [Asserts AWS Exporter](https://app.gitbook.com/o/-Mih12_HEHZ0gGyaqQ0X/s/-Mih17ZSkwF7P2VxUo4u/quickstart-guide/setting-up-aws-serverless-monitoring) is deployed |
|`ASSERTS_TENANT_NAME`|The tenant name in the Asserts Cloud where the metrics will be ingested |
|`ASSERTS_PASSWORD`|If the endpoint supports and expects Basic authorization the credentials can be configured here |

# Exported Metrics

The following metrics are exported by this layer

|Metric Name|Metric Type|Description|
|-----------|------|-----|
|`aws_lambda_invocations_total`| `Counter` | The count of invocations on this Lambda instance |
|`aws_lambda_errors_total`| `Counter` | The count of invocations on this Lambda instance that resulted in an error |
|`aws_lambda_duration_seconds`| `Histogram` | A histogram of the duration of the invocations  |

In addition to the above metrics, the process metrics collected by [client_python](https://github.com/prometheus/client_python) are also exported.
