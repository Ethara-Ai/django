from contextlib import contextmanager

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import modify_settings, override_settings
from django.test.selenium import SeleniumTestCase
from django.utils.csp import CSP
from django.utils.translation import gettext as _

# Make unittest ignore frames in this module when reporting failures.
__unittest = True


@modify_settings(
    MIDDLEWARE={"append": "django.middleware.csp.ContentSecurityPolicyMiddleware"}
)
@override_settings(
    SECURE_CSP={
        "default-src": [CSP.NONE],
        "connect-src": [CSP.SELF],
        "img-src": [CSP.SELF],
        "script-src": [CSP.SELF],
        "style-src": [CSP.SELF],
    },
)
class AdminSeleniumTestCase(SeleniumTestCase, StaticLiveServerTestCase):
    available_apps = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.sites",
    ]

    def tearDown(self):
        # Ensure that no CSP violations were logged in the browser.
        pass

    def wait_until(self, callback, timeout=10):
        """
        Block the execution of the tests until the specified callback returns a
        value that is not falsy. This method can be called, for example, after
        clicking a link or submitting a form. See the other public methods that
        call this function for more details.
        """
        pass

    def wait_for_and_switch_to_popup(self, num_windows=2, timeout=10):
        """
        Block until `num_windows` are present and are ready (usually 2, but can
        be overridden in the case of pop-ups opening other pop-ups). Switch the
        current window to the new pop-up.
        """
        pass

    def wait_for(self, css_selector, timeout=10):
        """
        Block until a CSS selector is found on the page.
        """
        pass

    def wait_for_text(self, css_selector, text, timeout=10):
        """
        Block until the text is found in the CSS selector.
        """
        pass

    def wait_for_value(self, css_selector, text, timeout=10):
        """
        Block until the value is found in the CSS selector.
        """
        pass

    def wait_until_visible(self, css_selector, timeout=10):
        """
        Block until the element described by the CSS selector is visible.
        """
        pass

    def wait_until_invisible(self, css_selector, timeout=10):
        """
        Block until the element described by the CSS selector is invisible.
        """
        pass

    def wait_page_ready(self, timeout=10):
        """
        Block until the page is ready.
        """
        pass

    @contextmanager
    def wait_page_loaded(self, timeout=10):
        """
        Block until a new page has loaded and is ready.
        """
        pass

    def trigger_resize(self):
        pass

    def admin_login(self, username, password, login_url="/admin/"):
        """
        Log in to the admin.
        """
        pass

    def select_option(self, selector, value):
        """
        Select the <OPTION> with the value `value` inside the <SELECT> widget
        identified by the CSS selector `selector`.
        """
        pass

    def deselect_option(self, selector, value):
        """
        Deselect the <OPTION> with the value `value` inside the <SELECT> widget
        identified by the CSS selector `selector`.
        """
        pass

    def assertCountSeleniumElements(self, selector, count, root_element=None):
        """
        Assert number of matches for a CSS selector.

        `root_element` allow restriction to a pre-selected node.
        """
        pass

    def _assertOptionsValues(self, options_selector, values):
        pass

    def assertSelectOptions(self, selector, values):
        """
        Assert that the <SELECT> widget identified by `selector` has the
        options with the given `values`.
        """
        pass

    def assertSelectedOptions(self, selector, values):
        """
        Assert that the <SELECT> widget identified by `selector` has the
        selected options with the given `values`.
        """
        pass

    def is_disabled(self, selector):
        """
        Return True if the element identified by `selector` has the `disabled`
        attribute.
        """
        pass
