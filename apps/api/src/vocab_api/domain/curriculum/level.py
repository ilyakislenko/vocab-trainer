from enum import StrEnum


class Level(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

    def order(self) -> int:
        return list(Level.__members__.values()).index(self)