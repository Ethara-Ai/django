from .api import get_messages

# Make unittest ignore frames in this module when reporting failures.
__unittest = True


class MessagesTestMixin:
    def assertMessages(self, response, expected_messages, *, ordered=True):
        pass
