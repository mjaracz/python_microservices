HANDLERS = {}

def MessagePattern(routing_key: str):
    def decorator(fn):
        HANDLERS[routing_key] = fn
        return fn
    return decorator
