from collections import defaultdict


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(
        self,
        event_type,
        handler,
    ):
        handler_key = (
            event_type,
            handler.__class__,
        )

        existing_handler_keys = [
            (
                registered_event_type,
                registered_handler.__class__,
            )
            for registered_event_type, handlers in self._handlers.items()
            for registered_handler in handlers
        ]

        if handler_key in existing_handler_keys:
            return

        self._handlers[event_type].append(handler)

    async def publish(
        self,
        event,
    ):
        handlers = self._handlers[type(event)]

        for handler in handlers:
            await handler.handle(event)


event_bus = EventBus()