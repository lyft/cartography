from functools import partial
from functools import wraps


def handle(func=None, on_error_return=[]):
    ERROR_CODES = [
        ZeroDivisionError,
    ]

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if type(e) in ERROR_CODES:
                print(f'supported error encountered {e}')
                return on_error_return
            else:
                raise
    if func is None:
        # return partial(handle, on_error_return=on_error_return)
        return lambda f: handle(f, on_error_return=on_error_return)
    return inner


@handle
def k():
    return 1 / 0


@handle(on_error_return=([], []))
def g():
    1 / 0


@handle(on_error_return='another_default')
def h():
    return {}['fake key']
