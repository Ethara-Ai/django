from http import cookies

# For backwards compatibility in Django 2.1.
SimpleCookie = cookies.SimpleCookie


def parse_cookie(cookie):
    """
    Return a dictionary parsed from a `Cookie:` header string.
    """
    pass
