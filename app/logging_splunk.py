import os
import json
import time
import urllib.request
from typing import Any, Dict, Optional

"""
Lightweight Splunk HEC helper for optional logging.

Environment variables (set by Terraform on Lambda or locally):
  SPLUNK_HEC_URL     Base URL or /services/collector/event endpoint
  SPLUNK_HEC_TOKEN   HEC token (sensitive)
  SPLUNK_INDEX       Optional index
  SPLUNK_SOURCE      Defaults to "fastapi"
  SPLUNK_SOURCETYPE  Defaults to "_json"
  SPLUNK_ENABLE      "1" (default) to enable, "0" to disable
"""

_raw_url = (os.getenv("SPLUNK_HEC_URL", "").strip().rstrip("/"))
_token = os.getenv("SPLUNK_HEC_TOKEN", "").strip()
_url = _raw_url
if _url:
    if _url.endswith("/event"):
        pass
    elif _url.endswith("/collector"):
        _url = f"{_url}/event"
    elif "/collector/" not in _url:
        _url = f"{_url}/services/collector/event"

_enabled = os.getenv("SPLUNK_ENABLE", "1") == "1" and bool(_url and _token)
_index = os.getenv("SPLUNK_INDEX", "").strip() or None
_source = os.getenv("SPLUNK_SOURCE", "fastapi")
_sourcetype = os.getenv("SPLUNK_SOURCETYPE", "_json")

def log_event(event_type: str, props: Optional[Dict[str, Any]] = None) -> None:
    if not _enabled:
        return
    payload: Dict[str, Any] = {
        "time": int(time.time()),
        "source": _source,
        "sourcetype": _sourcetype,
        "event": {"type": event_type, **(props or {})},
    }
    if _index:
        payload["index"] = _index
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(_url, data=data, method="POST")
        req.add_header("Authorization", f"Splunk {_token}")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=1.0).read()
    except Exception:
        # Silent failure by design
        pass
