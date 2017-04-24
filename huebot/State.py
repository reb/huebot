"""State module that tracks and handles state changes."""

_failures = set()
_warnings = set()


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
        warning_before = is_warning()
        normal_before = is_normal()
        func(*args)
        print("failures:", _failures, "warnings:", _warnings)
        failure_after = is_failure()
        warning_after = is_warning()
        normal_after = is_normal()

        if not failure_before and failure_after:
            __on_failure()

        if not warning_before and warning_after:
            __on_warning()

        if not normal_before and normal_after:
            __on_normal()

    return add_observer


@_observe
def failure(key):
    """Set the status to failure for the given key."""
    _failures.add(key)


@_observe
def warning(key):
    """Set the status to warning for the given key."""
    try:
        _failures.remove(key)
    except KeyError:
        pass

    _warnings.add(key)


@_observe
def normal(key):
    """Return the status to normal for the given key."""
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
    return len(_warnings) > 0 and len(_failures) == 0


def is_normal():
    """Return the current warning status."""
    return len(_failures) == 0 and len(_warnings) == 0
