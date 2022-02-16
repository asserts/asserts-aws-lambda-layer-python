import os


def islayer_disabled():
    valid = {'true': True, 'false': False, }
    layer_disabled = False
    value = os.environ.get('ASSERTS_LAYER_DISABLED')
    if value is not None:
        lower_value = value.lower()
        if lower_value in valid:
            layer_disabled = valid[lower_value]
    return layer_disabled
