"""Task 25: JSON log formatter (stdlib ล้วน) สำหรับ production."""
import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """log บรรทัดละ JSON: timestamp/level/logger/message."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
