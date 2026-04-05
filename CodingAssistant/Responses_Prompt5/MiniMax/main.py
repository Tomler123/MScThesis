"""
EventEmitter - A simple event emitter implementation.
"""

from typing import Callable, Any


class EventEmitter:
    """
    A simple event emitter supporting on, off, once, and emit.

    This class provides a publish/subscribe pattern for event handling,
    allowing callbacks to be registered, unregistered, and triggered
    for specific events.
    """

    def __init__(self) -> None:
        """Initialize the EventEmitter with an empty listeners dictionary."""
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event.

        The same callback can be registered multiple times and will fire
        that many times when the event is emitted.

        Args:
            event: The name of the event to listen for.
            callback: The callable to invoke when the event is emitted.
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """
        Remove one registration of the callback for the event.

        If the callback is not registered, this does nothing.

        Args:
            event: The name of the event.
            callback: The callback to remove.
        """
        if event not in self._listeners:
            return

        try:
            self._listeners[event].remove(callback)
        except ValueError:
            pass  # Callback not in list, do nothing

    def once(self, event: str, callback: Callable) -> None:
        """
        Register a callback that fires at most once, then auto-removes itself.

        When the event is emitted, the callback is invoked and then
        automatically removed. If the event is never emitted, the
        callback remains registered until removed via off().

        Args:
            event: The name of the event to listen for.
            callback: The callable to invoke once when the event is emitted.
        """
        if event not in self._listeners:
            self._listeners[event] = []

        # Wrap the callback to auto-remove after execution
        def wrapper(*args: Any, **kwargs: Any) -> None:
            callback(*args, **kwargs)
            # Remove this wrapper (and thus the original callback) from listeners
            try:
                self._listeners[event].remove(wrapper)
            except ValueError:
                pass

        # Replace callback with wrapper for later removal
        self._listeners[event].append(wrapper)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Call all registered callbacks for the event with the given arguments.

        Callbacks are invoked in registration order. If no listeners are
        registered for the event, this does nothing.

        Args:
            event: The name of the event to emit.
            *args: Positional arguments to pass to each callback.
            **kwargs: Keyword arguments to pass to each callback.
        """
        if event not in self._listeners:
            return

        # Iterate over a copy of the list to safely handle
        # callbacks that modify the listener list (e.g., once callbacks)
        for callback in self._listeners[event][:]:
            callback(*args, **kwargs)


# Run tests if executed directly
if __name__ == "__main__":
    results = []

    # Basic on/emit
    em = EventEmitter()
    em.on("data", lambda x: results.append(x))
    em.emit("data", 1)
    em.emit("data", 2)
    assert results == [1, 2], f"Test 1 failed: {results}"
    print("Test 1 passed: Basic on/emit")

    # Multiple listeners
    results.clear()
    em2 = EventEmitter()
    em2.on("e", lambda: results.append("a"))
    em2.on("e", lambda: results.append("b"))
    em2.emit("e")
    assert results == ["a", "b"], f"Test 2 failed: {results}"
    print("Test 2 passed: Multiple listeners")

    # off removes one registration
    results.clear()
    em3 = EventEmitter()

    def handler(x):
        results.append(x)

    em3.on("e", handler)
    em3.on("e", handler)
    em3.emit("e", 1)
    assert results == [1, 1], f"Test 3a failed: {results}"
    em3.off("e", handler)
    results.clear()
    em3.emit("e", 2)
    assert results == [2], f"Test 3b failed: {results}"
    print("Test 3 passed: off removes one registration")

    # off on non-existent does nothing
    em4 = EventEmitter()
    em4.off("nope", lambda: None)  # no error
    print("Test 4 passed: off on non-existent does nothing")

    # once fires only once
    results.clear()
    em5 = EventEmitter()
    em5.once("e", lambda x: results.append(x))
    em5.emit("e", 10)
    em5.emit("e", 20)
    assert results == [10], f"Test 5 failed: {results}"
    print("Test 5 passed: once fires only once")

    # emit with no listeners
    em6 = EventEmitter()
    em6.emit("nothing")  # no error
    print("Test 6 passed: emit with no listeners")

    # once + on together
    results.clear()
    em7 = EventEmitter()
    em7.on("e", lambda: results.append("on"))
    em7.once("e", lambda: results.append("once"))
    em7.emit("e")
    em7.emit("e")
    assert results == ["on", "once", "on"], f"Test 7 failed: {results}"
    print("Test 7 passed: once + on together")

    # emit unknown event
    em8 = EventEmitter()
    em8.emit("x", 1, 2, key="val")  # no error, no crash
    print("Test 8 passed: emit unknown event")

    # kwargs forwarding
    results.clear()
    em9 = EventEmitter()
    em9.on("e", lambda a, b=0: results.append(a + b))
    em9.emit("e", 3, b=7)
    assert results == [10], f"Test 9 failed: {results}"
    print("Test 9 passed: kwargs forwarding")

    print("\nAll tests passed!")
