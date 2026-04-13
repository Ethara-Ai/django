from urllib.parse import quote

from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.template import Context, Engine, TemplateDoesNotExist, loader
from django.views.decorators.csrf import requires_csrf_token

ERROR_404_TEMPLATE_NAME = "404.html"
ERROR_403_TEMPLATE_NAME = "403.html"
ERROR_400_TEMPLATE_NAME = "400.html"
ERROR_500_TEMPLATE_NAME = "500.html"
ERROR_PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <title>%(title)s</title>
</head>
<body>
  <h1>%(title)s</h1><p>%(details)s</p>
</body>
</html>
"""


# These views can be called when CsrfViewMiddleware.process_view() not run,
# therefore need @requires_csrf_token in case the template needs
# {% csrf_token %}.


@requires_csrf_token
def page_not_found(request, exception, template_name=ERROR_404_TEMPLATE_NAME):
    """
    Default 404 handler.

    Templates: :template:`404.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/'). It's
            quoted to prevent a content injection attack.
        exception
            The message from the exception which triggered the 404 (if one was
            supplied), or the exception class name
    """
    pass


@requires_csrf_token
def server_error(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: None
    """
    pass


@requires_csrf_token
def bad_request(request, exception, template_name=ERROR_400_TEMPLATE_NAME):
    """
    400 error handler.

    Templates: :template:`400.html`
    Context: None
    """
    pass


@requires_csrf_token
def permission_denied(request, exception, template_name=ERROR_403_TEMPLATE_NAME):
    """
    Permission denied (403) handler.

    Templates: :template:`403.html`
    Context:
        exception
            The message from the exception which triggered the 403 (if one was
            supplied).

    If the template does not exist, an Http403 response containing the text
    "403 Forbidden" (as per RFC 9110 Section 15.5.4) will be returned.
    """
    pass
