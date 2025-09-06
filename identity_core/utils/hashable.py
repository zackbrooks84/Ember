# identity_core/utils/hashable.py
from typing import Any

def to_immutable(x: Any) -> Any:
    """
    Convert dicts, lists, sets, and tuples into hashable, stable forms.
    dict -> tuple of sorted (key, value) pairs, with values converted too
    list/set/tuple -> tuple of converted items
    everything else -> returned as is
    """
    if isinstance(x, dict):
        return tuple(sorted((k, to_immutable(v)) for k, v in x.items()))
    if isinstance(x, (list, tuple, set)):
        return tuple(to_immutable(v) for v in x)
    return x