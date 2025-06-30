import threading
from collections import defaultdict

class EventManager:
    _singleton = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            with cls._lock:
                # Double-checked locking
                if not cls._singleton:
                    cls._singleton = super().__new__(cls)
                    cls._singleton._initialized = False
        return cls._singleton

    def __init__(self):
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return
            self.event_callbacks = defaultdict(list)
            self._initialized = True

    def emit(self, event: int, data: dict):
        # The original used Qt.QueuedConnection, which is async.
        # Direct calling is sync. For a backend, this is often simpler and acceptable.
        # A copy is made to prevent issues if a handler modifies the list during iteration.
        if event in self.event_callbacks:
            for handler in self.event_callbacks[event][:]:
                try:
                    handler(event, data)
                except Exception as e:
                    # In a real app, you'd want to log this properly.
                    print(f"Error in event handler for event {event}: {e}")

    def subscribe(self, event: int, handler: callable):
        with self._lock:
            if handler not in self.event_callbacks[event]:
                self.event_callbacks[event].append(handler)

    def unsubscribe(self, event: int, handler: callable):
        with self._lock:
            if event in self.event_callbacks and handler in self.event_callbacks[event]:
                self.event_callbacks[event].remove(handler)
