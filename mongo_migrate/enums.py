import enum


class Direction(str, enum.Enum):
    up = "upgrade"
    down = "downgrade"