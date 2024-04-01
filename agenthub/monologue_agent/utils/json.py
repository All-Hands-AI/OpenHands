import json
from json_repair import repair_json

def my_encoder(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()

def dumps(obj, **kwargs):
    return json.dumps(obj, default=my_encoder, **kwargs)

def loads(s, **kwargs):
    s_repaired = repair_json(s)

    if s_repaired != s:
        print(f"Repaired JSON: {s_repaired}")
        print(f"Original JSON: {s}")

    return json.loads(s_repaired, **kwargs)

