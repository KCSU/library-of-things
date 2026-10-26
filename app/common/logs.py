"""Structured log lines for Cloud Logging."""

import json
import logging
import os
from datetime import UTC, datetime


def on_cloud_run() -> bool:
    return bool(os.getenv('K_SERVICE') or os.getenv('CLOUD_RUN_JOB'))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if record.exc_info:
            message += '\n' + self.formatException(record.exc_info)
        if record.stack_info:
            message += '\n' + self.formatStack(record.stack_info)
        return json.dumps(
            {
                'severity': record.levelname,
                'message': message,
                'logger': record.name,
                'time': datetime.fromtimestamp(record.created, UTC).isoformat(),
            }
        )
