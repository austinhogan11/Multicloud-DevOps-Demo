import os
import json
import time
import urllib.request
from typing import Any, Dict, Optional
try:
  import boto3  # type: ignore
except Exception:
  boto3 = None

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
_secret_arn = os.getenv("SPLUNK_HEC_SECRET_ARN", "").strip()
_secret_name = os.getenv("SPLUNK_HEC_SECRET_NAME", "").strip()
_url = _raw_url
if _url:
    if _url.endswith("/event"):
        pass
    elif _url.endswith("/collector"):
        _url = f"{_url}/event"
    elif "/collector/" not in _url:
        _url = f"{_url}/services/collector/event"

_enabled = os.getenv("SPLUNK_ENABLE", "1") == "1" and bool(_url)
_index = os.getenv("SPLUNK_INDEX", "").strip() or None
_source = os.getenv("SPLUNK_SOURCE", "fastapi")
_sourcetype = os.getenv("SPLUNK_SOURCETYPE", "_json")

_cached_token: Optional[str] = _token or None
_last_fetch_ts: float = 0.0
_TOKEN_TTL = 300.0  # seconds

def _get_token() -> Optional[str]:
    global _cached_token, _last_fetch_ts
    # Prefer explicit token if provided
    if _cached_token:
        return _cached_token
    # Fetch from Secrets Manager if configured
    if not (_secret_arn or _secret_name) or boto3 is None:
        return None
    now = time.time()
    if _cached_token and (now - _last_fetch_ts) < _TOKEN_TTL:
        return _cached_token
    try:
        client = boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=_secret_arn or _secret_name)
        secret_string = resp.get("SecretString")
        # Accept either raw string or JSON object with hec_token key
        token = None
        if secret_string:
            token = secret_string
            try:
                obj = json.loads(secret_string)
                token = obj.get("hec_token") or obj.get("token") or secret_string
            except Exception:
                pass
        _cached_token = token
        _last_fetch_ts = now
        return _cached_token
    except Exception:
        return None

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
        token = _get_token()
        if not token:
            return
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(_url, data=data, method="POST")
        req.add_header("Authorization", f"Splunk {token}")
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=1.0).read()
    except Exception:
        # Silent failure by design
        pass
