import enum
from enum import EnumType, IntEnum, StrEnum
from enum import property as enum_property

from django.utils.functional import Promise

__all__ = ["Choices", "IntegerChoices", "TextChoices"]


class ChoicesType(EnumType):
    """A metaclass for creating a enum choices."""

    def __new__(metacls, classname, bases, classdict, **kwds):
        labels = []
        for key in classdict._member_names:
            value = classdict[key]
            if (
                isinstance(value, (list, tuple))
                and len(value) > 1
                and isinstance(value[-1], (Promise, str))
            ):
                *value, label = value
                value = tuple(value)
            else:
                label = key.replace("_", " ").title()
            labels.append(label)
            # Use dict.__setitem__() to suppress defenses against double
            # assignment in enum's classdict.
            dict.__setitem__(classdict, key, value)
        cls = super().__new__(metacls, classname, bases, classdict, **kwds)
        for member, label in zip(cls.__members__.values(), labels):
            member._label_ = label
        return enum.unique(cls)

    @property
    def names(cls):
        pass

    @property
    def choices(cls):
        pass

    @property
    def labels(cls):
        pass

    @property
    def values(cls):
        return [value for value, _ in cls.choices]


class Choices(enum.Enum, metaclass=ChoicesType):
    """Class for creating enumerated choices."""

    do_not_call_in_templates = enum.nonmember(True)

    @enum_property
    def label(self):
        pass

    # A similar format was proposed for Python 3.10.
    def __repr__(self):
        return f"{self.__class__.__qualname__}.{self._name_}"


class IntegerChoices(Choices, IntEnum):
    """Class for creating enumerated integer choices."""

    pass


class TextChoices(Choices, StrEnum):
    """Class for creating enumerated string choices."""

    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        pass
