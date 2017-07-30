"""State module concerning the status of the tracked channels."""


def _observe(func):
    """
    Decorate functions with an observer pattern.

    Checks the failure status before and after executing the decorated
    function. If it changed, execute the proper callback.
    """
    def add_observer(self, *args):
        """Check the failure status and handle accordingly."""
        failure_before = self.is_failure()
        warning_before = self.is_warning()
        normal_before = self.is_normal()
        func(self, *args)
        failure_after = self.is_failure()
        warning_after = self.is_warning()
        normal_after = self.is_normal()

        if not failure_before and failure_after:
            self.on_failure()

        if not warning_before and warning_after:
            self.on_warning()

        if not normal_before and normal_after:
            self.on_normal()

    return add_observer


class State:
    """State object that tracks and handles state changes."""

    def __init__(self):
        """Create the State object."""
        self._failures = set()
        self._warnings = set()

        def do_nothing():
            """Default callback handler."""
            pass

        self.on_failure = do_nothing
        self.on_warning = do_nothing
        self.on_normal = do_nothing

        self.on_new_failure = do_nothing
        self.on_new_warning = do_nothing

    @_observe
    def failure(self, key):
        """Set the status to failure for the given key."""
        if key not in self._failures:
            self._failures.add(key)
            self.on_new_failure(key)

    @_observe
    def warning(self, key):
        """Set the status to warning for the given key."""
        try:
            self._failures.remove(key)
        except KeyError:
            pass

        if key not in self._warnings:
            self._warnings.add(key)
            self.on_new_warning(key)

    @_observe
    def normal(self, key):
        """Return the status to normal for the given key."""
        try:
            self._failures.remove(key)
        except KeyError:
            pass

        try:
            self._warnings.remove(key)
        except KeyError:
            pass

    def is_failure(self):
        """Return the current failure status."""
        return len(self._failures) > 0

    def is_warning(self):
        """Return the current warning status."""
        return len(self._warnings) > 0 and len(self._failures) == 0

    def is_normal(self):
        """Return the current warning status."""
        return len(self._failures) == 0 and len(self._warnings) == 0
