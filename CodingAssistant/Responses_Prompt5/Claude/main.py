from typing import Callable, Dict, List, Any
from collections import defaultdict


class EventEmitter:
    """A simple event emitter supporting on, off, once, and emit."""

    def __init__(self) -> None:
        # Each event maps to a list of [callback, is_once] pairs
        self._listeners: Dict[str, List[List]] = defaultdict(list)

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event.

        The same callback can be registered multiple times and will fire
        once for each registration.

        Args:
            event: The event name to listen for.
            callback: The callable to invoke when the event is emitted.
        """
        self._listeners[event].append([callback, False])

    def off(self, event: str, callback: Callable) -> None:
        """Remove one registration of a callback for the given event.

        If the callback is not registered for the event, does nothing.

        Args:
            event: The event name.
            callback: The callable to remove (one occurrence only).
        """
        listeners = self._listeners.get(event)
        if not listeners:
            return
        for i, (cb, _) in enumerate(listeners):
            if cb is callback:
                listeners.pop(i)
                return

    def once(self, event: str, callback: Callable) -> None:
        """Register a callback that fires at most once, then removes itself.

        Args:
            event: The event name to listen for.
            callback: The callable to invoke once when the event is emitted.
        """
        self._listeners[event].append([callback, True])

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Call all registered callbacks for the event with the given arguments.

        Callbacks are called in registration order. 'once' listeners are
        removed after firing. Emitting an event with no listeners is a no-op.

        Args:
            event: The event name to emit.
            *args: Positional arguments forwarded to each callback.
            **kwargs: Keyword arguments forwarded to each callback.
        """
        listeners = self._listeners.get(event)
        if not listeners:
            return
        # Snapshot the list to safely iterate while once-listeners self-remove
        for entry in list(listeners):
            cb, is_once = entry
            if is_once:
                try:
                    listeners.remove(entry)
                except ValueError:
                    pass
            cb(*args, **kwargs)