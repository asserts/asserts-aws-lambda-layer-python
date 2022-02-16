
import sys
import logging
from datetime import datetime
from asserts_pylambda.LambdaMetrics import LambdaMetrics
from asserts_pylambda.AssertsUtils import islayer_disabled

logger = logging.getLogger()


def reraise(tp, value, tb=None):
    # type: (Optional[Type[BaseException]], Optional[BaseException], Optional[Any]) -> None
    assert value is not None
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value


def _wrap_init_error(init_error):
    # type: (F) -> F
    def sentry_init_error(*args, **kwargs):
        # type: (*Any, **Any) -> Any
        return init_error(*args, **kwargs)

    return sentry_init_error  # type: ignore


def _wrap_handler(handler):
    # type: (F) -> F
    def asserts_handler(aws_event, aws_context, *args, **kwargs):
        # type: (Any, Any, *Any, **Any) -> Any
        metrics = LambdaMetrics()
        error_raised = False
        try:
            start_time = datetime.now()
            metrics.recordInvocation()
            return handler(aws_event, aws_context, *args, **kwargs)
        except Exception:
            exc_info = sys.exc_info()
            error_raised = True
            reraise(*exc_info)
        finally:
            if error_raised:
                metrics.recordError()
            diff_time = datetime.now() - start_time
            metrics.recordLatency(diff_time.total_seconds())

    return asserts_handler


class AssertsLambdaPython():
    def __init__(self):
        layer_disabled = islayer_disabled()
        if layer_disabled:
            return
        lambda_bootstrap = get_lambda_bootstrap()
        if not lambda_bootstrap:
            logger.warning(
                "Not running in AWS Lambda environment, "
                "AwsLambdaIntegration disabled (could not find bootstrap module)"
            )
            return

        if not hasattr(lambda_bootstrap, "handle_event_request"):
            logger.warning(
                "Not running in AWS Lambda environment, "
                "AwsLambdaIntegration disabled (could not find handle_event_request)"
            )
            return

        pre_37 = hasattr(lambda_bootstrap, "handle_http_request")  # Python 3.6 or 2.7
        if pre_37:
            old_handle_event_request = lambda_bootstrap.handle_event_request

            def asserts_handle_event_request(request_handler, *args, **kwargs):
                # type: (Any, *Any, **Any) -> Any
                request_handler = _wrap_handler(request_handler)
                return old_handle_event_request(request_handler, *args, **kwargs)

            lambda_bootstrap.handle_event_request = asserts_handle_event_request

            old_handle_http_request = lambda_bootstrap.handle_http_request

            def asserts_handle_http_request(request_handler, *args, **kwargs):
                # type: (Any, *Any, **Any) -> Any
                request_handler = _wrap_handler(request_handler)
                return old_handle_http_request(request_handler, *args, **kwargs)

            lambda_bootstrap.handle_http_request = asserts_handle_http_request

            # Patch to_json to drain the queue. This should work even when the
            # SDK is initialized inside of the handler

            old_to_json = lambda_bootstrap.to_json

            def asserts_to_json(*args, **kwargs):
                # type: (*Any, **Any) -> Any
                # _drain_queue()
                return old_to_json(*args, **kwargs)

            lambda_bootstrap.to_json = asserts_to_json
        else:
            lambda_bootstrap.LambdaRuntimeClient.post_init_error = _wrap_init_error(
                lambda_bootstrap.LambdaRuntimeClient.post_init_error
            )

            old_handle_event_request = lambda_bootstrap.handle_event_request

            def asserts_handle_event_request(  # type: ignore
                    lambda_runtime_client, request_handler, *args, **kwargs
            ):
                request_handler = _wrap_handler(request_handler)
                return old_handle_event_request(
                    lambda_runtime_client, request_handler, *args, **kwargs
                )

            lambda_bootstrap.handle_event_request = asserts_handle_event_request

            # Patch the runtime client to drain the queue. This should work
            # even when the SDK is initialized inside of the handler

            def _wrap_post_function(f):
                # type: (F) -> F
                def inner(*args, **kwargs):
                    # type: (*Any, **Any) -> Any
                    # _drain_queue()
                    return f(*args, **kwargs)

                return inner  # type: ignore

            lambda_bootstrap.LambdaRuntimeClient.post_invocation_result = (
                _wrap_post_function(
                    lambda_bootstrap.LambdaRuntimeClient.post_invocation_result
                )
            )
            lambda_bootstrap.LambdaRuntimeClient.post_invocation_error = (
                _wrap_post_function(
                    lambda_bootstrap.LambdaRuntimeClient.post_invocation_error
                )
            )


def get_lambda_bootstrap():
    # type: () -> Optional[Any]

    # Python 2.7: Everything is in `__main__`.
    #
    # Python 3.7: If the bootstrap module is *already imported*, it is the
    # one we actually want to use (no idea what's in __main__)
    #
    # Python 3.8: bootstrap is also importable, but will be the same file
    # as __main__ imported under a different name:
    #
    #     sys.modules['__main__'].__file__ == sys.modules['bootstrap'].__file__
    #     sys.modules['__main__'] is not sys.modules['bootstrap']
    #
    # Python 3.9: bootstrap is in __main__.awslambdaricmain
    #
    # On container builds using the `aws-lambda-python-runtime-interface-client`
    # (awslamdaric) module, bootstrap is located in sys.modules['__main__'].bootstrap
    #
    # Such a setup would then make all monkeypatches useless.
    if "bootstrap" in sys.modules:
        logger.info('bootstrap')
        return sys.modules["bootstrap"]
    elif "__main__" in sys.modules:
        module = sys.modules["__main__"]
        # python3.9 runtime
        if hasattr(module, "awslambdaricmain") and hasattr(
                module.awslambdaricmain, "bootstrap"  # type: ignore
        ):
            logger.info('awslambdaricmain')
            return module.awslambdaricmain.bootstrap  # type: ignore
        elif hasattr(module, "bootstrap"):
            # awslambdaric python module in container builds
            logger.info('module.bootstrap')
            return module.bootstrap  # type: ignore

        # python3.8 runtime
        return module
    else:
        return None
