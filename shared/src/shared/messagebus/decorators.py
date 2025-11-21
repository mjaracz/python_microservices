HANDLERS = {}


def RPCHandler(routing_key: str):
    def decorator(func):
        func.__rpc_handler__ = routing_key
        return func
    return decorator

def EventHandler(routing_key: str):
    def decorator(func):
        func.__event_handler__ = routing_key
        return func
    return decorator