from typing import Callable, Any

class EventEmitter:
    """A simple event emitter supporting on, off, once, and emit."""

    def __init__(self) -> None:
        # Stores a list of (callback, is_once_flag) tuples for each event
        self._events: dict[str, list[tuple[Callable[..., Any], bool]]] = {}

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        """Register a callback for an event."""
        self._events.setdefault(event, []).append((callback, False))

    def off(self, event: str, callback: Callable[..., Any]) -> None:
        """Remove one registration of the callback for the event."""
        if event not in self._events:
            return
        
        for i, (cb, _) in enumerate(self._events[event]):
            if cb == callback:
                del self._events[event][i]
                break

    def once(self, event: str, callback: Callable[..., Any]) -> None:
        """Register a callback that fires at most once, then auto-removes itself."""
        self._events.setdefault(event, []).append((callback, True))

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Call all registered callbacks for the event with the given arguments."""
        if event not in self._events:
            return
        
        # Iterate over a shallow copy to safely handle removals during iteration
        for item in list(self._events[event]):
            cb, is_once = item
            cb(*args, **kwargs)
            
            if is_once:
                try:
                    self._events[event].remove(item)
                except ValueError:
                    # Ignore if the callback already removed itself via .off()
                    pass