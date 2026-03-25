import json
from hashlib import sha256


def normalize_mapping(mapping):
    if not mapping:
        return {}

    if hasattr(mapping, "lists"):
        normalized = {}
        for key, values in mapping.lists():
            normalized[key] = values if len(values) > 1 else values[0]
        return normalized

    normalized = {}
    for key, value in mapping.items():
        normalized[key] = list(value) if isinstance(value, tuple) else value
    return normalized


def stable_digest(payload):
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()
