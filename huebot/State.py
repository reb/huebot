"""State module that tracks and handles state changes."""

_failures = set()


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
        func(*args)
        print("failures:", _failures)
        failure_after = is_failure()

        if failure_before and not failure_after:
            __on_normal()

        if not failure_before and failure_after:
            __on_failure()

    return add_observer


@_observe
def failure(key):
    """Add a failure for the given key."""
    _failures.add(key)


@_observe
def normal(key):
    """Remove any status for the given key."""
    try:
        _failures.remove(key)
    except KeyError:
        pass


def is_failure():
    """Return the current failure status."""
    return len(_failures) > 0
