from __future__ import annotations
import base64
import json
import sys
import traceback
from typing import Any, Dict

from wformat.wformat import WFormat


class WFormatDaemon:
    """
    Persistent stdio daemon for wformat.
    JSON Lines protocol (one JSON object per line).

    Requests:
    {"id": 1, "op": "format", "b64": "<source>"}
    {"id": 2, "op": "ping"}
    {"op": "shutdown"}

    Replies:
    {"id": 1, "ok": true,  "b64": "<formatted>"}
    {"id": 1, "ok": false, "error": "<message>"}
    {"id": 2, "ok": true}
    {"ok": true}  # for shutdown
    """

    _MAX_REQUEST_BYTES = 16 * 1024 * 1024

    def __init__(self, formatter: WFormat) -> None:
        self.wformat = formatter

    def _reply(self, obj: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def _reply_err(self, msg: str, rid: int | None = None) -> None:
        payload: Dict[str, Any] = {"ok": False, "error": msg}
        if rid is not None:
            payload["id"] = rid
        self._reply(payload)

    def serve(self) -> int:
        try:
            for raw in sys.stdin:
                line = raw.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except Exception as e:
                    self._reply_err(f"bad json: {e.__class__.__name__}: {e}")
                    continue

                op = req.get("op")
                rid = req.get("id")

                try:
                    if op == "shutdown":
                        self._reply({"ok": True})
                        return 0

                    if op == "ping":
                        self._reply({"id": rid, "ok": True})
                        continue

                    if op == "format":
                        raw_text: str | None = None
                        b64 = req.get("b64")

                        try:
                            in_bytes = base64.b64decode(b64, validate=True)
                        except Exception:
                            self._reply_err("invalid base64 in 'b64'", rid)
                            continue

                        if len(in_bytes) > self._MAX_REQUEST_BYTES:
                            self._reply_err("request too large", rid)
                            continue

                        raw_text = in_bytes.decode("utf-8", "replace")

                        try:
                            out_text = self.wformat.format_memory(raw_text)
                        except Exception:
                            sys.stderr.write("format failed:\n")
                            sys.stderr.write(traceback.format_exc())
                            sys.stderr.flush()
                            self._reply_err("internal error", rid)
                            continue
                        sys.stderr.flush()
                        out_b64 = base64.b64encode(
                            out_text.encode("utf-8", "replace")
                        ).decode("ascii")
                        self._reply({"id": rid, "ok": True, "b64": out_b64})
                        continue

                    self._reply_err(f"unknown op: {op}", rid)

                except Exception:
                    sys.stderr.write("daemon crash:\n")
                    sys.stderr.write(traceback.format_exc())
                    sys.stderr.flush()
                    self._reply_err("internal error", rid)

        except KeyboardInterrupt:
            return 0
        return 0
