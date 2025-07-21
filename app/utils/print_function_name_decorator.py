from pprint import pprint
import os

# TODO(MFB): Instead of hard-coded booleans, we should use a config file / environment variable.
IS_PRINT_FILE_LINK= True # This will not work, as it's giving the Docker path.
IS_ADJUST_TO_STACK = True

def get_host_path(container_path):
    host_path = os.getenv('HOST_PATH')
    if not host_path:
        return container_path
    if container_path.startswith('/app/'):
        # Replace only the prefix
        if host_path.endswith('/'):
            host_path = host_path[:-1]
        return container_path.replace('/app/', host_path + '/', 1)
    return container_path  # Already a host path, do not modify

def get_embedded_file_link(func):
    file_path = os.path.abspath(func.__code__.co_filename)
    host_path = get_host_path(file_path)
    # Ensure three slashes after file:
    uri = f"file://{host_path}" if host_path.startswith('/') else f"file:///{host_path}"
    return f"\033]8;;{uri}\033\\{func.__name__}\033]8;;\033\\"

def print_def_name(should_print=True):
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
    def decorator(func):
        if not should_print:
            # If we shouldn't print, just return the original function unchanged
            return func

        if IS_ADJUST_TO_STACK:
            import functools
            import inspect

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Subtract 1 to not count the wrapper itself
                depth = max(1, len(inspect.stack()) - 9)
                print('')
                if IS_PRINT_FILE_LINK:
                    print(
                        f"{'_' * depth * 2} {get_embedded_file_link(func)} {'_' * depth * 2}")
                else:
                    print(f"{'_' * depth * 2} {func.__name__} {'_' * depth * 2}")

                return func(*args, **kwargs)
            return wrapper
        else:
            def wrapper(*args, **kwargs):
                print('')
                if IS_PRINT_FILE_LINK:
                    print(f"______ {get_embedded_file_link(func)} ______")
                else:
                    print(f"______ {func.__name__} ______")
                return func(*args, **kwargs)
            return wrapper

    # Handle the case where the decorator is used without parentheses
    # e.g., @print_def_name instead of @print_def_name()
    if callable(should_print):
        # In this case, should_print is actually the function being decorated
        func = should_print
        should_print = True  # Default behavior
        return decorator(func)

    return decorator

def print_main_def_name(func):
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
    def wrapper(*args, **kwargs):
        print(f"-- Args:")
        pprint(args)
        print(f"-- Kwargs:")
        pprint(kwargs)
        return func(*args, **kwargs)
    return wrapper
