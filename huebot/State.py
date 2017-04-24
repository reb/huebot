"""State module that tracks and handles state changes."""

_failures = set()
_warnings = set()


def __none():
    pass

__on_failure = __none
__on_warning = __none
__on_normal = __none


def __set(handler):
    def set_handler(callback):
        nonlocal handler
        handler = callback
    return set_handler


set_on_failure = __set(__on_failure)
set_on_warning = __set(__on_warning)
set_on_normal = __set(__on_warning)


def _observe(func):
    """
    Decorate functions with an observer pattern.

    Checks the failure status before and after executing the decorated
    function. If it changed, execute the proper callback.
    """
    def add_observer(*args):
        """Check the failure status and handle accordingly."""
        failure_before = is_failure()
        warning_before = is_warning()
        normal_before = is_normal()
        func(*args)
        print("failures:", _failures)
        print("warnings:", _failures)
        failure_after = is_failure()
        warning_after = is_warning()
        normal_after = is_normal()

        if (warning_before or normal_before) and failure_after:
            __on_failure()

        if (failure_before or normal_before) and warning_after:
            __on_warning()

        if (failure_before or warning_before) and normal_after:
            __on_normal()

    return add_observer


@_observe
def failure(key):
    """Add a failure for the given key."""
    _failures.add(key)


@_observe
def warning(key):
    """Add a warning for the given key."""
    _warnings.add(key)


@_observe
def normal(key):
    """Remove any status for the given key."""
    try:
        _failures.remove(key)
    except KeyError:
        pass

    try:
        _warnings.remove(key)
    except KeyError:
        pass


def is_failure():
    """Return the current failure status."""
    return len(_failures) > 0


def is_warning():
    """Return the current warning status."""
    return len(_warnings) > 0 and len(_warnings) == 0


def is_normal():
    """Return the current warning status."""
    return len(_failures) == 0 and len(_warnings) == 0
