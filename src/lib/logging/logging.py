"""Shared structured logging for command-line pipelines."""

import logging
import os
import sys
import traceback

import structlog
from pydantic import ValidationError

_secrets: tuple[str, ...] = ()


def register_secrets(*values: str) -> None:
    global _secrets
    _secrets = tuple(value for value in values if value)


def _exception_details(logger, method_name, event):
    exc_info = event.pop("exc_info", None)
    if exc_info:
        info = sys.exc_info() if exc_info is True else exc_info
        error = info[1]
        if error is not None:
            event["error_type"] = type(error).__name__
            if isinstance(error, ValidationError):
                event["validation_errors"] = error.errors(
                    include_input=False, include_context=False, include_url=False
                )
                event["error"] = f"{error.error_count()} validation error(s)"
            else:
                event["error"] = str(error)
            # No locals or raw Pydantic inputs (configuration may contain secrets).
            frames = traceback.extract_tb(info[2])
            event["traceback"] = "\n".join(
                f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in frames
            )
            if frames:
                frame = frames[-1]
                event["failure_location"] = (
                    f"{frame.filename}:{frame.lineno} in {frame.name}"
                )
            cause = error.__cause__ or (
                None if error.__suppress_context__ else error.__context__
            )
            if cause:
                event["cause_type"] = type(cause).__name__
                event["cause"] = (
                    f"{cause.error_count()} validation error(s)"
                    if isinstance(cause, ValidationError)
                    else str(cause)
                )
    return event


def _redact(logger, method_name, event):
    def clean(value):
        if isinstance(value, str):
            for secret in _secrets:
                value = value.replace(secret, "[REDACTED]")
            return value
        if isinstance(value, dict):
            return {key: clean(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [clean(item) for item in value]
        return value

    return clean(event)


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ValueError(f"Unsupported LOG_LEVEL: {level}")
    log_format = os.getenv("LOG_FORMAT", "console").lower()
    if log_format not in {"console", "json"}:
        raise ValueError(f"Unsupported LOG_FORMAT: {log_format}")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            _exception_details,
            _redact,
            structlog.processors.JSONRenderer(ensure_ascii=False)
            if log_format == "json"
            else structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )
