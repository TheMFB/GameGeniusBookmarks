import os
import threading
from functools import wraps
from typing import Callable, TypeVar, cast

from app.utils.printing_utils import pprint

IS_SILENCE_PRINT_DEF_NAME = True
IS_PRINT_FILE_LINK= True
IS_ADJUST_TO_STACK = True

F = TypeVar("F", bound=Callable[..., object])

def get_embedded_file_link(func):
    file_path = os.path.abspath(func.__code__.co_filename)

    # Ensure three slashes after file:
    uri = f"file://{file_path}" if file_path.startswith(
        '/') else f"file:///{file_path}"
    return f"\033]8;;{uri}\033\\{func.__name__}\033]8;;\033\\"

# Thread-local storage to track depth
_local = threading.local()
_local.depth = 0  # Default value

def print_def_name(should_print: bool = True) -> Callable[[F], F]:
    """
    This will print the function name and the file path.
    It will also print the file path in a clickable link.
    It will also print the function name and the file path in a clickable link.
    It will also print the function name and the file path in a clickable link.

    Args:
        should_print (bool): Whether to actually print the function name. Default is True.
                           Can be used like @print_def_name(not IS_DEBUG) to conditionally disable.

    Note that if you want to get it to open through Cursor, you may need to `brew install duti`, and select Cursor as the default app for .py files.
    """
    def decorator(func: F) -> F:
        if not should_print or IS_SILENCE_PRINT_DEF_NAME:
            return func

        @wraps(func)
        def wrapper(*args, **kwargs):
            depth = getattr(_local, 'depth', 0)

            # Print header
            print()
            if IS_PRINT_FILE_LINK:
                real_func = func
                print(f"{'_' * (depth * 2)} {get_embedded_file_link(real_func)} {'_' * (depth * 2)}")
            else:
                print(f"{'_' * (depth * 2)} {func.__name__} {'_' * (depth * 2)}")

            # Increment depth before calling
            _local.depth = depth + 1
            try:
                return func(*args, **kwargs)
            finally:
                # Decrement after call completes
                _local.depth = depth

        return cast(F, wrapper)

    if callable(should_print):
        # Decorator used without parentheses
        return decorator(should_print)  # type: ignore

    return decorator

def print_main_def_name(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print('')
        print('')
        if IS_PRINT_FILE_LINK:
            print(f"========= {get_embedded_file_link(func)} ==========")
        else:
            print(f"========= {func.__name__} ==========")
        print('')
        return func(*args, **kwargs)
    return wrapper


def print_def_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("-- Args:")
        pprint(args)
        print("-- Kwargs:")
        pprint(kwargs)
        return func(*args, **kwargs)
    return wrapper


def only_run_once(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal has_run
        if not has_run:
            has_run = True
            return func(*args, **kwargs)
        return None
    has_run = False
    return wrapper

def make_hashable(obj):
    if isinstance(obj, (tuple, list)):
        return tuple(make_hashable(e) for e in obj)
    if isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    return obj

def memoize(func):
    """
    Decorator to cache function results in memory for the duration of the process,
    keyed by the function's arguments and keyword arguments.
    """
    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        hashable_args = make_hashable(args)
        hashable_kwargs = make_hashable(kwargs)
        key = (hashable_args, hashable_kwargs)
        if key in cache:
            return cache[key]
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    return wrapper
