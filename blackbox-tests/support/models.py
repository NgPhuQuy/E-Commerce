from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"


@dataclass(frozen=True, slots=True)
class TestUser:
    email: str
    password: str
    token: str
    role: Role
