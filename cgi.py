"""
Minimal compatibility shim for the removed `cgi` stdlib module (Python 3.14+).
Only implements `parse_header` which `httpx` needs for content-type parsing.

This file lives in the project root so it is importable from the working
directory and provides the minimal API expected by downstream packages.
"""
from typing import Tuple, Dict, Optional


def _strip_quotes(val: str) -> str:
    if len(val) >= 2 and (val[0] == val[-1]) and val[0] in ('"', "'"):
        return val[1:-1]
    return val


def parse_header(line: Optional[str]) -> Tuple[str, Dict[str, str]]:
    """Parse a Content-Type like header into (value, params dict).

    This intentionally implements a small, forgiving subset of the
    original stdlib behavior that is sufficient for `httpx`'s usage.
    """
    if not line:
        return "", {}

    parts = [p.strip() for p in line.split(";")]
    value = parts[0]
    params: Dict[str, str] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.strip().lower()] = _strip_quotes(v.strip())
        else:
            params[part.strip().lower()] = ""

    return value, params
