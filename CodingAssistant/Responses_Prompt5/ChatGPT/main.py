from typing import Any, Callable


class EventEmitter:
    """A simple event emitter supporting on, off, once, and emit."""

    class _Listener:
        """Internal listener record."""

        def __init__(self, callback: Callable[..., Any], once: bool = False) -> None:
            self.callback = callback
            self.once = once

    def __init__(self) -> None:
        """Initialize an empty event emitter."""
        self._events: dict[str, list[EventEmitter._Listener]] = {}

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Register a callback for an event."""
        self._events.setdefault(event, []).append(self._Listener(callback, once=False))

    def off(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove one registration of the callback for the event, if present."""
        listeners = self._events.get(event)
        if not listeners:
            return

        for i, listener in enumerate(listeners):
            if listener.callback is callback:
                del listeners[i]
                if not listeners:
                    del self._events[event]
                return

    def once(self, event: str, callback: Callable[..., Any]) -> None:
        """Register a callback that is called at most once for the event."""
        self._events.setdefault(event, []).append(self._Listener(callback, once=True))

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Call all registered callbacks for the event in registration order."""
        listeners = self._events.get(event)
        if not listeners:
            return

        # Iterate over a snapshot so removals during emission do not break ordering.
        snapshot = listeners[:]

        for listener in snapshot:
            listener.callback(*args, **kwargs)
            if listener.once:
                current_listeners = self._events.get(event)
                if current_listeners and listener in current_listeners:
                    current_listeners.remove(listener)
                    if not current_listeners:
                        del self._events[event]