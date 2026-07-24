import enum


class Direction(str, enum.Enum):
    up = "upgrade"
    down = "downgrade"

class Target(str, enum.Enum):
    head = "head"
    base = "base"

class BaseFlag(str, enum.Enum):
    """
    Flag used to represent base which corresponds to no timestamp.
    """
    base = "base"

    def __str__(self) -> str:
        return self.value    