import json
def safe_json(obj):
    return json.dumps(obj, default=str)
