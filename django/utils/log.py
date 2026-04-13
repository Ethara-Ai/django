import logging
import logging.config  # needed when logging_config doesn't start with logging.config
from copy import copy

from django.conf import settings
from django.core import mail
from django.core.mail import get_connection
from django.core.management.color import color_style
from django.utils.module_loading import import_string

request_logger = logging.getLogger("django.request")

# Default logging for Django. This sends an email to the site admins on every
# HTTP 500 error. Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded (DEBUG=False) by means of the
# require_debug_true filter. This configuration is quoted in
# docs/ref/logging.txt; please amend it there if edited here.
DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "mail_admins"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def configure_logging(logging_config, logging_settings):
    if logging_config:
        # First find the logging configuration function ...
        logging_config_func = import_string(logging_config)

        logging.config.dictConfig(DEFAULT_LOGGING)

        # ... then invoke it with the logging settings
        if logging_settings:
            logging_config_func(logging_settings)


class AdminEmailHandler(logging.Handler):
    """An exception log handler that emails log entries to site admins.

    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """

    def __init__(self, include_html=False, email_backend=None, reporter_class=None):
        super().__init__()
        self.include_html = include_html
        self.email_backend = email_backend
        self.reporter_class = import_string(
            reporter_class or settings.DEFAULT_EXCEPTION_REPORTER
        )

    def emit(self, record):
        # Early return when no email will be sent.
        pass

    def send_mail(self, subject, message, *args, **kwargs):
        mail.mail_admins(
            subject, message, *args, connection=self.connection(), **kwargs
        )

    def connection(self):
        return get_connection(backend=self.email_backend, fail_silently=True)

    def format_subject(self, subject):
        """
        Escape CR and LF characters.
        """
        pass


class CallbackFilter(logging.Filter):
    """
    A logging filter that checks the return value of a given callable (which
    takes the record-to-be-logged as its only parameter) to decide whether to
    log a record.
    """

    def __init__(self, callback):
        self.callback = callback

    def filter(self, record):
        pass


class RequireDebugFalse(logging.Filter):
    def filter(self, record):
        pass


class RequireDebugTrue(logging.Filter):
    def filter(self, record):
        pass


class ServerFormatter(logging.Formatter):
    default_time_format = "%d/%b/%Y %H:%M:%S"

    def __init__(self, *args, **kwargs):
        self.style = color_style()
        super().__init__(*args, **kwargs)

    def format(self, record):
        pass

    def uses_server_time(self):
        pass


def log_message(
    logger,
    message,
    *args,
    level=None,
    status_code=None,
    request=None,
    exception=None,
    **extra,
):
    """Log `message` using `logger` based on `status_code` and logger `level`.

    Pass `request`, `status_code` (if defined) and any provided `extra` as such
    to the logging method,

    Arguments from `args` will be escaped to avoid potential log injections.

    """
    extra = {"request": request, **extra}
    if status_code is not None:
        extra["status_code"] = status_code
        if level is None:
            if status_code >= 500:
                level = "error"
            elif status_code >= 400:
                level = "warning"

    escaped_args = tuple(
        a.encode("unicode_escape").decode("ascii") if isinstance(a, str) else a
        for a in args
    )

    getattr(logger, level or "info")(
        message,
        *escaped_args,
        extra=extra,
        exc_info=exception,
    )


def log_response(
    message,
    *args,
    response=None,
    request=None,
    logger=request_logger,
    level=None,
    exception=None,
):
    """
    Log errors based on HttpResponse status.

    Log 5xx responses as errors and 4xx responses as warnings (unless a level
    is given as a keyword argument). The HttpResponse status_code and the
    request are passed to the logger's extra parameter.
    """
    # Check if the response has already been logged. Multiple requests to log
    # the same response can be received in some cases, e.g., when the
    # response is the result of an exception and is logged when the exception
    # is caught, to record the exception.
    if getattr(response, "_has_been_logged", False):
        return

    log_message(
        logger,
        message,
        *args,
        level=level,
        status_code=response.status_code,
        request=request,
        exception=exception,
    )
    response._has_been_logged = True
