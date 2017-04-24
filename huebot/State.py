"""State module that tracks and handles state changes."""

_failures = set()


def __none():
    pass

__on_failure = __none
__on_warning = __none
__on_normal = __none


def set_on_failure(callback):
    """Set the function to call when the state changes to failure."""
    global __on_failure
    __on_failure = callback


def set_on_warning(callback):
    """Set the function to call when the state changes to warning."""
    global __on_warning
    __on_warning = callback


def set_on_normal(callback):
    """Set the function to call when the state changes to normal."""
    global __on_normal
    __on_normal = callback


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
