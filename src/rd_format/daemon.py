from __future__ import annotations
import json
import sys
import time
import traceback
from typing import Any, Dict

from rd_format.rd_format import RdFormat


class RdFormatDaemon:
    """
    Persistent stdio daemon for rd-format.
    JSON Lines protocol (one JSON object per line).

    Requests:
    {"id": 1, "op": "format", "text": "<source>"}
    {"id": 2, "op": "ping"}
    {"op": "shutdown"}

    Replies:
    {"id": 1, "ok": true,  "text": "<formatted>", "ms": 12.34}
    {"id": 2, "ok": true}
    {"ok": true}  # for shutdown
    {"id": 1, "ok": false, "error": "<message>"}
    """

    # 16 MiB hard cap for incoming text
    _MAX_REQUEST_BYTES = 16 * 1024 * 1024

    def __init__(self, rd: RdFormat) -> None:
        self.rd_format = rd

    # --- helpers -------------------------------------------------------------

    def _reply(self, obj: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def _reply_err(self, msg: str, rid: int | None = None) -> None:
        payload: Dict[str, Any] = {"ok": False, "error": msg}
        if rid is not None:
            payload["id"] = rid
        self._reply(payload)

    # --- main loop -----------------------------------------------------------

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
                        text = req.get("text")
                        if not isinstance(text, str):
                            self._reply_err("field 'text' must be a string", rid)
                            continue
                        if len(text.encode("utf-8")) > self._MAX_REQUEST_BYTES:
                            self._reply_err("request too large", rid)
                            continue

                        t0 = time.perf_counter()
                        try:
                            out_text = self.rd_format.format_memory(text)
                        except Exception:
                            sys.stderr.write("[rd-format] format failed:\n")
                            sys.stderr.write(traceback.format_exc())
                            sys.stderr.flush()
                            self._reply_err("internal error", rid)
                            continue
                        dt = (time.perf_counter() - t0) * 1000.0
                        self._reply(
                            {
                                "id": rid,
                                "ok": True,
                                "text": out_text,
                                "ms": round(dt, 2),
                            }
                        )
                        continue

                    self._reply_err(f"unknown op: {op}", rid)

                except Exception:
                    sys.stderr.write("[rd-format] daemon crash:\n")
                    sys.stderr.write(traceback.format_exc())
                    sys.stderr.flush()
                    self._reply_err("internal error", rid)

        except KeyboardInterrupt:
            return 0
        return 0
